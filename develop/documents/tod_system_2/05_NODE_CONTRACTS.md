# 04_NODE_CONTRACTS - Dialogue System Design Pack
本章は **ノード仕様** を定義する。


## 1. Conventions（記法）
### 1.1 Node Spec Template
- **Purpose**：ノードの責務（1〜2行）
<!-- - **Inputs（Reads）**：読むStateキー
- **Outputs（Writes Δ）**：書くStateキー（差分Δ）
- **Side Effects**：外部I/O（API/DB/キュー）
- **Preconditions**：前提（必要なスロット等）
- **Postconditions**：事後条件（更新されたこと、整合条件）
- **Failure Handling**：例外・リトライ・fallback/handoff
- **Observability**：ログ/メトリクスに出すべき項目
- **Tests**：単体/統合の観点（15への参照） -->


---


## 2. Node Topology（ノード群の俯瞰）
> Fallback Nodeに関しては図からは割愛しています。

```mermaid
flowchart TD
  U[User msg]

  subgraph NLU["NLU"]
    IR["IR<br/>(Intent Recognition)"]
  end

  subgraph DM["DM - Dialogue Manager"]
    subgraph DST["DST - State Tracking"]
      GST["GST<br/>(Goal State Tracking)"]
      SST["SST<br/>(Slot State Tracking)"]
    end

    subgraph DAE["DAE - Dialogue Act Executor"]
      SE["SE<br/>(Slot-filling Executor)"]
      GE["GE<br/>(Goal Executor)"]
    end

    subgraph DP["DP - Dialogue Policy"]
      SP["SP<br/>(Slot-filling Policy)"]
      GP["GP<br/>(Goal Policy)"]
    end
  end

  U --> SG[SG<br>（Start Gate）]
  SG --> IR
  IR --> |"intent_type not in [OOS, QUESTION, SMALL_TALK]"|GST
  IR -->|"intent_type in [OOS, QUESTION, SMALL_TALK]"| NP["NP<br/>(Non-tod Policy)"]
  GST -->|"dialogue_mode==SLOT_FILLING"| SST
  GST -->|"dialogue_mode==STEP_BY_STEP"| GE
  SST --> SE
  SE --> SP
  GE --> GP
  SP --> GP
  GP --> RP[Response Proxy]
  NP --> RP
  RP --> RN
  subgraph NLG["NLG"]
    RN["Response Nodes"]
  end
  RN --> EG[EG<br>（End Gate）]
  EG --> R[Response msg]
````

---

## 4. Node Specs（個別仕様）

> 詳細は後日追記。現時点では Node Name と Purpose のみ。

---

### 4.0 Gate Nodes

各ターンの開始と終わりで共通の State 更新を行う。

#### SG — START GATE
* **Node Name**: `SG`
* **Purpose**: ターン開始時の共通処理（chat_history へのユーザーメッセージ追加、Guardrails 入力検証など）

#### EG — END GATE
* **Node Name**: `EG`
* **Purpose**: ターン終了時の共通処理（chat_history への AI 応答追加、Guardrails 出力検証など）

---

### 4.1 NLU — Natural Language Understanding

#### IR — Intent Recognition
* **Node Name**: `IR`
* **Purpose**: ユーザー発話から意図（intent_type）を推定する

---

### 4.2 DM (DST) — Dialogue State Tracking

#### GST — Goal State Tracker
* **Node Name**: `GST`
* **Purpose**: intent と文脈から、対話モード（dialogue_mode）の初期決定を行う

#### SST — Slot State Tracker
* **Node Name**: `SST`
* **Purpose**: 発話からスロットを抽出し、不足スロットを更新する

---

### 4.3 DM (DAE) — Dialogue Act Executor

#### SE — Slot-filling Executor
* **Node Name**: `SE`
* **Purpose**: スロット充填モードの実行部。ツールへ接続するための入力を整える

#### GE — Goal Executor
* **Node Name**: `GE`
* **Purpose**: planに従い、ツール呼び出し前の入力形成・実行段取りを行う

---

### 4.4 DM (DP) — Dialogue Policy

#### SP — Slot-filling Policy
* **Node Name**: `SP`
* **Purpose**: 不足スロットを埋めるための次アクション（確認質問/実行）を決める

#### GP — Goal Policy
* **Node Name**: `GP`
* **Purpose**: STEP_BY_STEPモードで次のステップ、分岐、ツール実行可否を決める
---

### 4.5 NLG — Natural Language Generation

#### RN — Response Nodes
* **Node Name**: `RN`
* **Purpose**: response を最終整形し、ユーザーへ返す応答を生成する

---

### 4.6 Other

#### NP — Non-task Policy
* **Node Name**: `NP`
* **Purpose**: OOS / QUESTION / SMALL_TALK の場合に、タスク本流とは別のポリシーで応答方針を決める

#### FB — Fallback Node
* **Node Name**: `FB`
* **Purpose**: 各ノードからのエラー/イレギュラーを受け、フォールバック応答を生成する


## 5. イレギュラーケース対応（Fallback Node）

すべてのノードでエラーやイレギュラーが発生した場合、**Fallback Node** を経由して適切な応答を生成する。

### 5.1 Fallback Node 概要

```mermaid
flowchart TD
  subgraph ORCH[Orchestrator]
    direction LR
    SG[START GATE] --> NLU --> DM --> NLG --> EG[END GATE]
    FB[Fallback Node]
  end

  NLU -->|理解不能| FB
  DM -->|不整合/例外| FB
  NLG -->|生成失敗| FB
  FB --> NLG
```

### 5.2 Fallback Node 仕様

* **Node ID**: `FB`
* **Purpose**: 各ノードからのエラー/イレギュラーを受け、適切なフォールバック応答を生成する
* **Inputs（Reads）**: `errors`, `chat_history`, `query`
* **Outputs（Writes Δ）**: `response`, `errors`（ログ追記）
* **Side Effects**: なし（テンプレート選択のみ）
* **Preconditions**: `errors` にエラー情報がセットされている

### 5.3 エラー種別と応答テンプレート

| エラー種別 | 発生元 | 応答例 |
|-----------|-------|--------|
| `MISUNDERSTANDING` | NLU | 「申し訳ありません。ご質問の意図を正しく理解できませんでした。もう少し詳しく教えていただけますか？」 |
| `CONTEXT_MISMATCH` | DM | 「お答えの内容と質問が一致していないようです。内容をご確認のうえ、もう一度ご回答いただけますか？」 |
| `INVALID_INPUT` | SST | 「入力内容に問題があるようです。正しい形式で入力してください。」 |
| `SLOT_EXTRACTION_FAILED` | SST | 「情報を正しく認識できませんでした。恐れ入りますが、もう一度お伝えいただけますか？」 |
| `GENERATION_FAILED` | NLG | 「申し訳ありません。応答の生成中に問題が発生しました。もう一度お試しください。」 |
| `TIMEOUT` | TOOL/外部 | 「処理に時間がかかっています。しばらくお待ちいただくか、もう一度お試しください。」 |
| `SYSTEM_ERROR` | 任意 | 「システムエラーが発生しました。お手数ですが、しばらく経ってから再度お試しください。」 |

### 5.4 処理フロー

```
1. ノードでエラー/イレギュラー検知
   ↓
2. errors に種別・発生元・詳細を記録
   ↓
3. Fallback Node へ遷移
   ↓
4. エラー種別に応じたテンプレート選択
   ↓
5. response にフォールバックメッセージをセット
   ↓
6. NLG → END GATE → Response
```

### 5.5 リトライとエスカレーション

| 条件 | 動作 |
|------|------|
| 同一エラーが **2回連続** | 表現を変えて再質問 |
| 同一エラーが **3回連続** | 「別の方法でサポートさせてください」＋話題転換 |
| システムエラー | 即座にフォールバック応答（リトライなし） |



## 6. Node R/W Matrix（StateのRead/Write契約・俯瞰）

> ノード名は 05_WORKFLOW_DM.md の用語に寄せる。
> Wは「主に更新責務を持つ」、Rは「参照する」。

### 6.1 各モジュールにおけるState Key

| State Key         | SG | NLU | DM  | NLG | EG | FB  | Notes            |
| ----------------- | --:   | --: | --: | --: | --: | --: | ---------------- |
| `query`           |   -   |   - |   - |   - |   - |   - | workflowのinvoke時に設定 |
| `response`        |   -   |   - |   - |   W |   - |   - | NLGの結果を保持      |
| `chat_history`    |   W   |   R |   R |   R |   W |   - | ユーザMSGとNLGの結果を保持.|
| `all_history`     |   W   |   W |   W |   W |   W |   - | デバッグ/分析用       |
| `intents`         |   W   |   R |   R |   R |   R |   - | -            |
| `dialogue_mode`   |   -   |   - |   W |   - |   - |   - | -            |
| `goal_phase`      |   -   |   - |   W |   - |   - |   - | -            |
| `step_contexts`   |   -   |   - |   W |   - |   - |   - | -            |
| `step_history`    |   -   |   - |   W |   - |   - |   - | -            |
| `slots_contexts`  |   -   |   - |   W |   - |   - |   - | -            |
| `slot_context`    |   -   |   - |   W |   - |   - |   - | -            |
| `errors`          |   -   |   - |   - |   - |   - |   W | 例外時のみ    |


### 6.2 DM(Dialogue Management)におけるState Key

| State Key         | DST<br>GST | <br>SST | DAE<br>GE | <br/>SE | DP<br>GP | <br>SP | Notes            |
| ----------------- | -:         | --:     | --:       | --:     | --:      | --:    | ---------------- |
| `query`           |  -         |   -     |   R       |   R     |  -       |  -     | ユーザー入力          |
| `response`        |  -         |   -     |   -       |   -     |  -       |  -     | AI応答             |
| `chat_history`    |  -         |   -     |   R       |   R     |  -       |  -     | append-only      |
| `all_history`     |  W         |   W     |   W       |   W     |  W       |  W     | デバッグ/分析用       |
| `intents`         |  R         |   -     |   -       |   -     |  -       |  -     | IR生成            |
| `dialogue_mode`   |  W         |   R     |   -       |   -     |  -       |  -     | GST/DP制御        |
| `goal_phase`      |  W         |   R     |   W       |   R     |  W       |  R     | GST/GE/GP更新     |
| `step_contexts`   |  W         |   -     |   W       |   -     |  R       |  -     | GST/GE更新        |
| `step_history`    |  R         |   -     |   W       |   -     |  R       |  -     | GE append        |
| `slots_contexts`  |  W         |   W     |   -       |   -     |  -       |  R     | SST/SE更新        |
| `slot_context`    |  -         |   W     |   -       |   W     |  -       |  W     | SST/SE/SP更新     |
| `errors`          |  -         |   -     |   -       |   -     |  -       |  -     | 例外時のみ         |
