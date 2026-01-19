# 07 Error Handling & Modes - Dialogue System

本ドキュメントは、対話システムの **例外処理（error handling）** と **モード（modes）** を定義する。  
ワークフロー（正常系）は `05_WORKFLOW_DM.md`、Stateのキーは `04_STATE_MODEL.md` を正とする。

---

## 1. Goals（このドキュメントの目的）
- 失敗時でも「破綻しない」対話を保証する（落ちない／無限ループしない／次の行動がわかる）
- 例外の分類と共通の扱い（どこへ遷移し、何をログに残し、いつ打ち切るか）を統一する
- `dialogue_mode`（SLOT_FILLING / STEP_BY_STEP）を含む “モード” を明確化し、運用可能にする

---

## 2. Modes（モード定義）

### 2.1 Primary Modes（主モード）
- `dialogue_mode = SLOT_FILLING`  
  - 目的：不足情報（slots）を収集・確定する
  - 主ノード：GST → SST → SE → SFP → GP
- `dialogue_mode = STEP_BY_STEP`  
  - 目的：ゴールを手順として進める（stepを実行する）
  - 主ノード：GST → GE → GP

> `dialogue_mode` は GST が決定する（正：`04_STATE_MODEL.md`）

### 2.2 Secondary Modes（副モード：推奨）
例外処理のために、副モード（Stateキー）は持っておくと運用が安定する。  
（キー名は `sub_mode` や `runtime_mode` など。`04_STATE_MODEL.md` 側で採用する。）

推奨の値：
- `NORMAL`：正常進行
- `FALLBACK`：聞き返し／やり直し
- `RETRYING`：外部失敗などのリトライ中
- `HANDOFF`：人手対応へ切替
- `TERMINAL`：終了（これ以上進めない）

---

## 3. Error Taxonomy（例外分類）

例外は原因により扱いが異なる。分類を統一する。

### 3.1 User-caused（ユーザ起因）
- 入力不足（必要slotが埋まらない）
- 矛盾（同一slotに矛盾値）
- 意図が曖昧／複数

**基本方針**
- clarification（確認質問）へ誘導
- 回数上限を超えたら HANDOFF または安全終了

### 3.2 External dependency（外部依存）
- APIタイムアウト
- 5xx / rate limit
- 認証失敗（期限切れ）

**基本方針**
- retry（指数バックオフなど）を許容
- 上限超過で HANDOFF または “今できない” 応答

### 3.3 Internal（内部不整合）
- State欠損（必要キーがない）
- ルーティング不可能（想定外のintent_type/dialogue_mode）
- 例外（コード例外）

**基本方針**
- safe fallback（安全応答）＋ログ/アラート
- 再現性が高いので迅速に改善対象

### 3.4 Policy / Safety（ポリシー・安全）
- 禁止事項の要求（危険行為、機密、権限外）
- ツール呼び出し禁止（許可外）

**基本方針**
- 断り／代替案提示（NPまたはRP経由）
- 必要に応じ HANDOFF

---

## 4. Common Handling Rules（共通処理ルール）

### 4.1 Always respond（必ず返す）
- 例外が起きても最終的に **RP → RN → EG** を通って応答を返す（沈黙しない）

### 4.2 Never infinite loop（無限ループ禁止）
- いずれのループも上限を持つ（clarify回数、retry回数、再実行回数）

推奨上限（初期値・調整可）：
- `max_clarify_turns = 3`
- `max_tool_retries = 2`
- `max_fallback_turns = 2`

> 上限値の正は `99_DECISIONS_LOG.md` に記録して運用で更新する。

### 4.3 Minimal state mutation on failure（失敗時はStateを壊さない）
- 失敗時に `slots` や `goal_state` を不用意に巻き戻さない  
- エラー情報は `error` に集約し、復旧可能かを明示する

推奨 `error` スキーマ（例）：
- `error.type`: user / external / internal / policy
- `error.code`: 例 `TIMEOUT`, `RATE_LIMIT`, `STATE_MISSING`
- `error.message`: 短い説明（ログ向け）
- `error.retryable`: bool
- `error.at_node`: IR/GST/SE/GE/SFP/GP/RN
- `error.counts`: retry_count / clarify_count など

---

## 5. Failure Points & Routing（失敗点ごとの遷移）

### 5.1 IR（Intent Recognition）
**典型失敗**
- intent_type 判定不能
- 低信頼（曖昧）

**遷移**
- 基本：NP（Non-task）へフォールバックし、「できること」を提示
- 代替：SFP的な “意図確認質問” を出す（運用方針次第）

**ユーザ向け応答の型**
- 「どちらの意味ですか？」（選択肢提示）
- 「何をしたいかもう少し教えてください」

---

### 5.2 GST（Goal State Tracking）
**典型失敗**
- dialogue_mode が決まらない
- goal_state が不整合

**遷移**
- FALLBACK：最小限の追加質問（目的の確認 / 前提の確認）
- internal不整合なら safe fallback + 収束（HANDOFF含む）

---

### 5.3 SST/SE（Slot path）
**典型失敗**
- slot値が抽出できない
- 矛盾（同じslotに矛盾値）
- 検証失敗（フォーマット不正）

**遷移**
- まず SFP へ（確認質問で回収）
- clarify上限超過 → HANDOFF または “完了できない” 応答

---

### 5.4 GE（Step-by-step path）
**典型失敗**
- 外部API失敗
- ステップ実行不能（前提が足りない）

**遷移**
- retry可能：RETRYING → 再実行（上限まで）
- retry不可：SLOT_FILLINGへ戻して前提を集める（可能なら）
- 上限超過：HANDOFF または安全終了

---

### 5.5 GP/SFP（Policy）
**典型失敗**
- next_action が不正
- response_plan が欠損
- ルーティング不能

**遷移**
- internal：safe fallback（固定テンプレ）へ
- 以降は必ず RP→RN に流し、ユーザへ次の一手を返す

---

### 5.6 RN（Response Nodes）
**典型失敗**
- 生成失敗（例外）
- 生成結果が空／不正

**遷移**
- safe response（固定文）へ切替
- ログ・アラートを上げる

---

## 6. Mode Transitions（モード遷移ルール）

### 6.1 SLOT_FILLING ↔ STEP_BY_STEP（基本）
- SLOT_FILLING は「前提情報が不足」しているときに入る
- STEP_BY_STEP は「前提が揃い、実行フェーズ」に入ったときに入る

**代表ルール**
- `missing_slots` が空になったら STEP_BY_STEP へ寄せる（GSTが決定）
- STEP_BY_STEP 中に前提不足が判明したら SLOT_FILLING へ戻す（GSTが決定）

### 6.2 Non-task（OOS/QUESTION/SMALL_TALK）
- `intent_type in [OOS, QUESTION, SMALL_TALK]` は DM に入らず NP を使う
- タスクへ戻す場合は「ユーザが明確にタスク意図を示したとき」のみ

---

## 7. Mermaid: Mode & Exception Overview（概要図）

「例外込みの大枠」を、仕様共有用に簡略化して示す（詳細はノード仕様に委譲）。

```mermaid
flowchart TD
  IR["IR"] -->|"intent_type in [OOS, QUESTION, SMALL_TALK]"| NP["NP"]
  IR -->|"task"| GST["GST"]

  GST -->|"dialogue_mode==SLOT_FILLING"| SLOT["SST -> SE -> SFP"]
  GST -->|"dialogue_mode==STEP_BY_STEP"| STEP["GE"]

  SLOT --> GP["GP"]
  STEP --> GP

  NP --> RP["RP -> RN -> EG"]
  GP --> RP

  IR -.-> FB["Fallback"]
  GST -.-> FB
  SLOT -.-> FB
  STEP -.-> RT["Retry"]
  RT -.-> HO["Handoff"]
  FB -.-> HO
````

> 注意：上図は “概念図” であり、正のワークフローは `05_WORKFLOW_DM.md`。

---

## 8. User-facing Response Patterns（ユーザ向けメッセージの型）

例外時の応答はテンプレで統一すると運用品質が上がる（RNで実装）。

### 8.1 Clarification（確認質問）

* 足りない情報を1〜2個に絞って質問
* 選択肢があるなら選択式にする

### 8.2 Temporary failure（外部失敗）

* 「いま実行できない」＋「再試行するか/後で試すか」
* 可能なら代替手段を提示

### 8.3 Safe fallback（内部不整合）

* 謝罪（短く）＋「できる範囲」＋「次に必要な情報」
* 必要ならサポート窓口/人手切替へ

### 8.4 Handoff（人手切替）

* 何が原因で自動処理できないか（簡潔）
* 何を渡すか（ケースID、要約、収集済み情報）

---

## 9. Observability Requirements（ログ/トレース要件：抜粋）

最低限ログに残す：

* `turn_id`
* `intent_type`
* `dialogue_mode`
* `next_action`
* `error.type / error.code / error.at_node`
* `clarify_count`, `retry_count`（上限管理用）
* ノードレイテンシ（成功/失敗）

PII方針：

* slotsの値は原則ログに出さない（スロット名のみ）

> 詳細は `14_OBSERVABILITY.md` と `13_SECURITY_AND_GUARDRAILS.md`。

---

## 10. Open Questions（運用で決める事項）

* clarify/retry/handoff の上限値（初期値は暫定）
* “意図確認質問” を NP でやるか、別ノードに切るか
* tool/API失敗時に SLOT_FILLING へ戻す条件（どの前提不足なら戻すか）
* HANDOFF のインタフェース（チケット、Slack、CRM等）

> 決定事項は `99_DECISIONS_LOG.md` に記録する。
