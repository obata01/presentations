# 03_STATE_SPEC - Dialogue System Design Pack
本章は **LangGraph State（状態）** の仕様です。  
**「Stateキー＝共通言語」** として、ノード間の契約（R/W）・ログ・テスト・運用の基準になります。  
※本章は **常に更新（Living Spec）** される前提です。

---

## 1. Purpose（この章の目的）
- LangGraphの State を **型・意味・初期値・更新ルール** まで含めて定義する
- ノード仕様（06）・DMフロー（05）・ログ（14）・テスト（15）に対して **唯一の参照点** を提供する
- State肥大化/PII混入/責務漏れを防ぐ

---

## 2. Principles（基本原則）
1) **State中心**：ノードは State を読み、差分（Δ）を書き戻す  
2) **差分更新**：ノードは `Δ`（Partial Update）のみ返し、オーケストレーターがマージする  
3) **小さく保つ**：外部データ全文は保持せず、要約＋参照IDを原則  
4) **PII最小化**：PIIは保存しない/マスクして保存（方針は13）  
5) **観測しやすく**：ログに出す項目（抜粋）をState側で固定する（14）

---

## 3. State Schema（全体像）
> 実装は `TypedDict` / `Pydantic` 等。ここでは概念設計（キー・型）を確定する。

```mermaid
classDiagram
  class State["State<br/>LangGraph State"]{
    ===== チャット情報 =====
    +str thread_id
    +str user_id
    +str query
    +str response
    +list[langchain_core.messages.BaseMessage] chat_history
    +list[Any] all_history
    ===== NLU制御 =====
    +list[IntentType] intents
    ===== Step-by-step制御 =====
    +DialogueMode dialogue_mode
    +GoalPhase goal_phase
    +dict[StepID, StepContext] step_contexts
    +list[GoalStepID] step_history
    ===== Slot-filling制御 =====
    +dict[str, SlotContext] slots_contexts
    +SlotContext slot_context
    ===== DP制御 =====
    +str next_slot
    ===== デバッグ用 =====
    +Errors errors 
  }

  class Intent["IntentType"]{
    ===== Sentiment intents =====
    +str ACKNOWLEDGE
    +str NEGATION
    ===== Command intents =====
    +str GOAL_TRIGGER
    +str TERMINATE
    +str NAVIGATION_NEXT
    +str NAVIGATION_BACK
    ===== Slot-filling intents =====
    +str SLOT_INFORM
    ===== NON-TOD intents =====
    +str QUESTION
    +str SMALL_TALK
    +str OSS
  }

  class DialogueMode["DialogueMode"]{
    +str SLOT_FILLING
    +str STEP_BY_STEP
  }

  class GoalPhase["GoalPhase"]{
    +str NOT_STARTED
    +str EXECUTION
    +str PENDING
    +str COMPLETED
    +str FAILED
  }

  class StepContext["StepContext"]{
    +str id
    +str phase
    +StepSchema info
    +Any action_result
  }

  class SlotContext["SlotContext"]{
    +str name
    +str phase
    +dict[str, Any]|SlotBase items
    +list[str] filled_items
    +list[str] missing_items
    +list[str] missing_optional_items  // 拡張用.
  }

  class Errors["Errors"]{
    +str error_type
    +str message
    +str node
    +str time_iso
  }

  State --> Intent
  State --> DialogueMode
  State --> GoalPhase
  State --> StepContext
  State --> SlotContext
  State --> Errors
````

---

## 4. State Keys（キー一覧・型・意味・初期値）

> 形式：**Key / Type / Meaning / Initial / Notes**

### 4.1 Chat Info（チャット情報）

| Key            | Type                | Meaning                     | Initial | Notes                 |
| -------------- | ------------------- | --------------------------- | ------- | --------------------- |
| `thread_id`    | `str`               | セッション識別子                    | 外部から注入  | 短期記憶のキー               |
| `user_id`      | `str`               | ユーザー識別子                     | 外部から注入  | -                     |
| `query`        | `str`               | ユーザー入力（クエリ）                 | `""`    | NLU入力                 |
| `response`     | `str`               | AI応答                        | `""`    | NLG出力                 |
| `chat_history` | `list[BaseMessage]` | 会話履歴（user/ai/tool）          | `[]`    | reducerで append       |
| `all_history`  | `list[Any]`         | 全履歴（内部状態含む）                 | `[]`    | デバッグ/分析用             |

### 4.2 NLU Control（NLU制御）

| Key      | Type         | Meaning | Initial                       | Notes             |
| -------- | ------------ | ------- | ----------------------------- | ----------------- |
| `intents` | `list[IntentType]` | 意図推定結果  | `[]` | - |

### 4.3 Step-by-Step Control（ステップ制御）

| Key             | Type                        | Meaning      | Initial          | Notes                           |
| --------------- | --------------------------- | ------------ | ---------------- | ------------------------------- |
| `dialogue_mode` | `DialogueMode`              | 対話モード        | `"SLOT_FILLING"` | SLOT_FILLING / STEP_BY_STEP     |
| `goal_phase`    | `GoalPhase`                 | ゴールフェーズ      | `"NOT_STARTED"`  | NOT_STARTED/PENDING/EXECUTION/COMPLETED/FAILED |
| `step_contexts` | `dict[StepID, StepContext]` | ステップ実行コンテキスト | `{}`             | ステップごとの状態管理                     |
| `step_history`  | `list[GoalStepID]`          | ステップ実行履歴     | `[]`             | 実行済みステップのID                     |

#### 4.3.1 Type Aliases（型エイリアス）

| Type         | Base   | Format                | Example                  |
| ------------ | ------ | --------------------- | ------------------------ |
| `StepID`     | `str`  | ステップ識別子               | `"confirm_info"`         |
| `GoalStepID` | `str`  | `goal_name:::step_id` | `"hearing:::confirm_info"` |

#### 4.3.2 StepContext Structure（StepContext構造）

| Field           | Type         | Meaning    |
| --------------- | ------------ | ---------- |
| `id`            | `str`        | ステップID     |
| `phase`         | `str`        | フェーズ（pending/executing/completed） |
| `info`          | `StepSchema` | ステップ定義情報   |
| `action_result` | `Any`        | アクション実行結果  |

### 4.4 Slot-Filling Control（スロット制御）

| Key              | Type                     | Meaning        | Initial | Notes           |
| ---------------- | ------------------------ | -------------- | ------- | --------------- |
| `slots_contexts` | `dict[str, SlotContext]` | 全スロットコンテキスト    | `{}`    | スロット名をキーとした辞書   |
| `slot_context`   | `SlotContext`            | 現在のスロットコンテキスト  | `None`  | アクティブなスロットの状態   |

#### 4.4.1 SlotContext Structure（SlotContext構造）

| Field                    | Type                         | Meaning                          |
| ------------------------ | ---------------------------- | -------------------------------- |
| `name`                   | `str`                        | スロット名                            |
| `phase`                  | `str`                        | フェーズ（pending/filling/completed） |
| `items`                  | `dict[str, Any] \| SlotBase` | スロット項目データ                        |
| `filled_items`           | `list[str]`                  | 入力済み項目リスト                        |
| `missing_items`          | `list[str]`                  | 未入力項目リスト                         |
| `missing_optional_items` | `list[str]`                  | 未入力オプション項目（拡張用）                  |

#### 4.4.2 Slot Terminology（スロット用語の階層）

| 用語             | 英語               | 意味                         | 例                                                       |
| -------------- | ---------------- | -------------------------- | ------------------------------------------------------- |
| **スロットコンテキスト群** | `slots_contexts` | すべてのSlotContextをまとめた辞書     | `{"current_job": SlotContext, "past_job": SlotContext}` |
| **スロットコンテキスト**  | `slot_context`   | 単一のスロット管理単位（状態・項目を保持）      | `SlotContext(name="current_job", phase="filling", ...)`  |
| **スロット項目**      | `item`           | スロット内の個別フィールド              | `company_name`, `position`, `salary`                    |

### 4.5 Debug / Error（デバッグ用）

| Key      | Type     | Meaning | Initial | Notes    |
| -------- | -------- | ------- | ------- | -------- |
| `errors` | `Errors` | エラー情報   | `{}`    | センシティブ禁止 |

#### 4.5.1 Errors Structure（Errors構造）

| Field        | Type  | Meaning     |
| ------------ | ----- | ----------- |
| `error_type` | `str` | エラー種別       |
| `message`    | `str` | エラーメッセージ    |
| `node`       | `str` | 発生ノード       |
| `time_iso`   | `str` | 発生時刻（ISO）   |

---

## 5. Reducers（マージ方針）

> LangGraphの state merge で衝突しやすいキーの扱いを固定する。

### 5.1 Reducer Table

| Key             | Reducer           | Policy                                |
| --------------- | ----------------- | ------------------------------------- |
| `chat_history`      | `add_messages` 相当 | **append-only**（削除しない）                |
