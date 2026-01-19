# 05 Workflow - DM (Dialogue Manager)

本ドキュメントは、対話システムの **ワークフロー（ノード遷移・分岐・合流）** を定義する。  
本書のMermaid図が「実装の正（source of truth）」となる。  
Stateキーの詳細は `04_STATE_MODEL.md`、ノード別の更新差分（Δ）は `06_NODE_SPECS.md` を参照。

---

## 1. Overview（全体像）

本システムは、ユーザ発話を受けて以下の流れで応答する。

- Start Gate → NLU（IR）
- intent_type が `OOS/QUESTION/SMALL_TALK` の場合：Non-task Policy（NP）→ Response Proxy（RP）→ Response Nodes（RN）
- タスクの場合：DM（DST/DAE/DP）を通過して RP→RN に合流
- End Gate でレスポンスを確定して返す

DM内部では、HierTOD風に **STEP_BY_STEP** と **SLOT_FILLING** を統合し、`dialogue_mode` により分岐する。

---

## 2. Source Workflow（Mermaid）

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

    subgraph DP["DP - Policy"]
      SFP["SFP<br/>(Slot-filling Policy)"]
      GP["GP<br/>(Goal Policy)"]
    end
  end

  U --> SG[Start Gate]
  SG --> IR
  IR --> |"intent_type not in [OOS, QUESTION, SMALL_TALK]"|GST
  IR -->|"intent_type in [OOS, QUESTION, SMALL_TALK]"| NP["NP<br/>(Non-task Policy)"]
  GST -->|"dialogue_mode==SLOT_FILLING"| SST
  GST -->|"dialogue_mode==STEP_BY_STEP"| GE
  SST --> SE
  SE --> SFP
  GE --> GP
  SFP --> GP
  GP --> RP[Response Proxy]
  NP --> RP
  RP --> RN
  subgraph NLG["NLG"]
    RN["Response Nodes"]
  end
  RN --> EG[End Gate]
  EG --> R[Response msg]
````

---

## 3. Branching Rules（分岐ルール）

### 3.1 intent_type による分岐（IR後）

* `intent_type in [OOS, QUESTION, SMALL_TALK]`

  * Non-task Policy（NP）へ遷移し、RPへ合流する
* `intent_type not in [OOS, QUESTION, SMALL_TALK]`

  * タスク系として GST（Goal State Tracking）へ遷移する

### 3.2 dialogue_mode による分岐（GST後）

* `dialogue_mode == SLOT_FILLING`

  * SST → SE → SFP → GP の順で進行し、GPへ合流する
* `dialogue_mode == STEP_BY_STEP`

  * GE → GP の順で進行し、GPへ合流する

---

## 4. Join Points（合流点）

* **GP と NP は Response Proxy（RP）に合流**する
* 応答生成は **RP → RN → EG** の経路に統一する（非タスクもタスクも同じ出口）

---

## 5. Responsibilities (high-level)（各ブロックの責務：概要）

詳細は `06_NODE_SPECS.md` に委譲し、本書では “遷移上の意味” のみ記す。

### NLU

* IR：intent_type を判定し、タスク/非タスクに分岐させる

### DM / DST

* GST：ゴール進行の追跡と、dialogue_mode の決定（SLOT_FILLING / STEP_BY_STEP）
* SST：スロット状態の追跡（slots / missing_slots の更新）

### DM / DAE

* SE：SLOT_FILLINGにおける、抽出・正規化・検証などの実行
* GE：STEP_BY_STEPにおける、手順ステップの実行

### DM / DP

* SFP：スロット充填の方針決定（確認質問/再質問/確定など）→ GPへ合流
* GP：タスク全体の方針決定（次ステップ/最終応答）→ RPへ

### NLG

* RP：応答生成の入口を統一し、適切な RN へルーティングする
* RN：具体の応答テキストを生成する

---

## 6. Error / Exception Hooks（例外の接続点：概要）

本図は “正常系の主経路” を表す。例外処理の詳細は `07_ERROR_HANDLING_AND_MODES.md` を正とする。
ただし、例外系が入りやすい接続点を以下に整理する。

* IR：intent_type 判定不能 → fallback / clarification（NP経由 or 専用経路）
* GST：dialogue_mode 決定不能 → fallback（質問・再入力）
* SE/GE：外部依存失敗 → retry / handoff / error response（GP/RP経由で返す）
* RN：生成失敗 → safe response（RP経由で統一）

---

## 7. Testing Checklist（この図で担保すべき最小テスト）

* Non-task:

  * intent_type = OOS → NP → RP → RN → EG
  * intent_type = QUESTION → NP → RP → RN → EG
  * intent_type = SMALL_TALK → NP → RP → RN → EG
* Task / SLOT_FILLING:

  * GST(dialogue_mode=SLOT_FILLING) → SST → SE → SFP → GP → RP → RN → EG
* Task / STEP_BY_STEP:

  * GST(dialogue_mode=STEP_BY_STEP) → GE → GP → RP → RN → EG

---

## 8. References（参照）

* Stateモデル（キー/型/reducer、read/write）: `04_STATE_MODEL.md`
* ノード仕様（Δ差分、入出力、失敗時）: `06_NODE_SPECS.md`
* 例外・モード・リトライ上限: `07_ERROR_HANDLING_AND_MODES.md`
* 評価・回帰: `11_EVALUATION_AND_METRICS.md` / `15_TEST_PLAN.md`


