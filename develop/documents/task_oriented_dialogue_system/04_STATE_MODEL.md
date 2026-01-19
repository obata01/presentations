# 04 State Model - Dialogue System (LangGraph State)

本ドキュメントは、LangGraphベース対話システムの **State（保持データ）** を定義する。  
ノードの責務・遷移は `05_WORKFLOW_DM.md`、ノード別の更新差分（Δ）は `06_NODE_SPECS.md` を正とする。

---

## 1. Design Principles（設計原則）

1) **Stateは「会話の真実（single source of truth）」**  
- 各ノードは State を read/write し、次のノードは State を入力として振る舞う。

2) **Stateは「小さく」「安定したキー」にする**  
- 大きな生データ（全文ログ、巨大な検索結果、バイナリ）は入れない。
- 参照が必要なら外部ストレージに置き、Stateには参照IDのみ保持する。

3) **更新は差分（Δ）で追跡できること**  
- どのノードがどのキーを更新するかは本書と `06_NODE_SPECS.md` で固定する。

4) **messages は reducer で append する**（推奨）  
- 会話履歴は “上書き” ではなく “追加”。
- それ以外のキーは原則「上書き更新」。

---

## 2. State Schema（キー定義）

以下は、本システムで推奨する最小～標準の State スキーマである。  
（実装は TypedDict でも Pydantic でもよい。型の正は本書。）

> 重要：`intent_type` / `dialogue_mode` はルーティングに直結するため、命名・意味を固定する。

### 2.1 Conversation / Routing

| Key | Type | Description | Owner (primary writer) |
|---|---|---|---|
| `ChatHistory` | list[Message] | 会話履歴（user/ai） | NLG(RN)（append） |
| `thread_id` | str / int | ターン識別子（任意） | Start Gate |
| `last_user_message` | str | 最新ユーザ発話（messagesから抽出してもOK） | Start Gate / IR |
| `last_ai_message` | str | 最新AI応答（messagesから抽出してもOK） | Start Gate / IR |

### 2.1.1 NLU(Natural Language Understanding)
| Key | Type | Description | Owner (primary writer) |
|---|---|---|---|
| `intent_type` | str | `OOS` / `QUESTION` / `SMALL_TALK` / task intent | IR |

### 2.2 Task State（Goal / Slot）

| Key | Type | Description | Owner (primary writer) |
|---|---|---|---|
| `dialogue_mode` | str | `SLOT_FILLING` / `STEP_BY_STEP` | GST | | 
| `goal_phase` | dict | 手順進行の状態（例：current_step, progress, history） | GST / GE |
| `slots` | dict[str, any] | 収集したスロット値 | SST / SE |
| `filled_slots` | list[str] | 収集したスロット値 | SST / SE |
| `missing_slots` | list[str] | 未充足スロット一覧（必須） | SST / SE |
| `action_history` | list[Any] | 実行したアクションの履歴 | SST / SE |


### 2.3 Policy / Response Planning

| Key | Type | Description | Owner (primary writer) |
|---|---|---|---|
| `nexts` | str | 次に取る行動（例：clarify/respond/execute_step） | SFP / GP / NP |
| `response_plan` | dict | RNに渡す「応答方針」(テンプレID/要点/トーン等) | NP / GP / SFP |
| `clarifying_question` | str? | 確認質問文（SLOT_FILLINGで使用） | SFP |

### 2.4 Execution / Tool（将来拡張を見越した枠）

| Key | Type | Description | Owner (primary writer) |
|---|---|---|---|
| `exec_trace` | list[dict] | 実行ログ（軽量） | GE / SE |
| `tool_calls` | list[dict] | 実行したツール呼び出し（軽量） | GE / SE |
| `tool_result` | dict? | 直近のツール結果（軽量） | GE / SE |
| `error` | dict? | 直近エラー（分類/メッセージ/リトライ可否等） | 各ノード |

> 実務では `tool_result` は巨大になりがちなので、ID参照（`tool_result_ref`）に寄せるのを推奨。

---

## 3. Reducer Rules（合成ルール）

### 3.1 messages
- reducer: append（例：LangGraph `add_messages`）
- 方針：
  - user入力は Start Gate で追加
  - assistant出力は RN で追加
  - toolメッセージ（使う場合）も append

### 3.2 その他キー
- 原則：最後に書いた値が勝つ（上書き）
- ただし以下は “追記型” でもよい：
  - `exec_trace`（append）
  - `tool_calls`（append）

---

## 4. Read/Write Matrix（ノード×キー）

「どのノードが何を読む/書くか」を固定し、設計と実装の齟齬を減らす。

### 4.1 Summary Table

| Node | Read | Write |
|---|---|---|
| Start Gate (SG) | request | `messages += user`, `user_text`, `turn_id` |
| IR | `user_text` / `messages` | `intent_type`, `entities` |
| NP | `intent_type`, `messages` | `next_action`, `response_plan` |
| GST | `intent_type`, `entities`, `goal_state` | `goal_state`, `dialogue_mode` |
| SST | `entities`, `slots`, `missing_slots` | `slots`, `missing_slots` |
| SE | `slots`, `missing_slots`, `entities` | `slots`, `missing_slots`, `exec_trace?` |
| GE | `goal_state`, `slots`, `entities` | `goal_state`, `exec_trace?`, `tool_*?`, `error?` |
| SFP | `slots`, `missing_slots` | `next_action`, `clarifying_question`, `response_plan` |
| GP | `goal_state`, `slots`, `error?` | `next_action`, `response_plan` |
| Response Proxy (RP) | `response_plan` | （基本はwriteなし） |
| Response Nodes (RN) | `response_plan`, `clarifying_question`, `goal_state`, `slots` | `final_answer`, `messages += assistant` |
| End Gate (EG) | `final_answer` / `messages` | response |

> 詳細な Δ（差分）と例外時の更新は `06_NODE_SPECS.md` を正とする。

---

## 5. Invariants（不変条件 / 整合性）

最低限、以下が満たされること。

### 5.1 Routing invariants
- `intent_type in [OOS, QUESTION, SMALL_TALK]` の場合、タスク系（GST）へは入らない
- `intent_type not in [OOS, QUESTION, SMALL_TALK]` の場合、NPのみで完結しない（原則GSTへ）

### 5.2 Mode invariants
- `dialogue_mode == SLOT_FILLING` の場合：
  - `missing_slots` は定義される（list）
  - SFPが `clarifying_question` または `response_plan` を作る
- `dialogue_mode == STEP_BY_STEP` の場合：
  - `goal_state.current_step` 相当が存在する（設計に依存）

### 5.3 Slot invariants
- `missing_slots` は `slots` と整合する（埋まったら減る／空ならslotの値が揃っている）
- `missing_slots` が空の場合、SFPは原則 “質問” を出さない（GPへ寄せる）

---

## 6. Logging Fields（ログに出す推奨フィールド）

可観測性のために、以下はログ/トレースに残す（ただしPIIはマスク）。

- `turn_id`
- `intent_type`
- `dialogue_mode`
- `next_action`
- `missing_slots`（スロット名のみ、値は原則出さない）
- `goal_state.current_step`（あれば）
- ノードレイテンシ、成功/失敗、`error.type`

---

## 7. PII / Sensitive Data（個人情報の扱い）

- `slots` にPII（住所・氏名など）が入り得るため、ログ出力は原則マスクまたは出力しない
- 外部ツール送信時は必要最小限にする
- State保持期間（TTL等）は `13_SECURITY_AND_GUARDRAILS.md` / `12_LLMOPS_AND_RELEASE.md` で定義する

---

## 8. Open Questions（State設計の未決事項）

- `goal_state` の標準フォーマット（current_step, plan, history の粒度）
- `entities` と `slots` の分離の粒度（どこでslot確定するか）
- `response_plan` のスキーマ（テンプレID中心か、自由テキスト中心か）
- `error` の分類体系（user/external/internal/policy など）
- tool結果の保持方式（ID参照に寄せるか）

> 決定事項は `99_DECISIONS_LOG.md` に記録する。
