# 01 Context & Scope - Dialogue System

本ドキュメントは、対話システムの「背景（Context）」と「対象範囲（Scope）」を定義する。  
要求（Must/Shall）や受入基準は `02_REQUIREMENTS.md` を正とする。

---

## 1. What we build（何を作るか）

LangGraphベースの対話システムを構築する。システムはユーザ発話を受けて、以下のワークフローで応答を返す。

- NLU: Intent Recognition（IR）
- DM（Dialogue Manager）: DST / DAE / DP を含む対話制御の中核
  - DST: GST（Goal State Tracking）, SST（Slot State Tracking）
  - DAE: GE（Goal Executor）, SE（Slot-filling Executor）
  - DP: GP（Goal Policy）, SFP（Slot-filling Policy）
- NLG: Response Proxy（RP）→ Response Nodes（RN）
- Gate: Start Gate（SG）, End Gate（EG）
- Non-task: Non-task Policy（NP）

> 具体のノード遷移・分岐は `05_WORKFLOW_DM.md` を正とする（本書では再掲しない）。

---

## 2. Why（なぜ作るか）

- タスク志向対話を「手順実行（STEP_BY_STEP）」と「情報収集（SLOT_FILLING）」の両方で扱うため
- OOS/QUESTION/SMALL_TALK 等の非タスクも、同一のNLG経路（RP→RN）で統一的に返すため
- Stateとノード責務を明文化し、実装・レビュー・運用の齟齬を減らすため

---

## 3. Use Cases（代表ユースケース）

### 3.1 Task-oriented（タスク志向）
- 手続き・業務フローの完遂（例：住所変更、申請、予約変更、求人提案 等）
- 特徴:
  - ゴール（goal）と手順（step）が存在する
  - 必要情報（slots）が揃わない場合はSLOT_FILLINGに切り替わる

### 3.2 Non-task（非タスク）
- `intent_type in [OOS, QUESTION, SMALL_TALK]` の応答（例：対象外要求、一般質問、FAQ、雑談）
- 特徴:
  - DMのタスク実行へは入らず、NP経由で応答方針を決める

---

## 4. Users / Stakeholders（想定ユーザ）

- End Users: 自然言語で用件を伝えたい利用者
- Implementer: LangGraphのState/ノードを実装
- Reviewer/PM: 仕様と要件の合意、優先順位付け
- Ops/SRE: ログ/監視/障害対応、リリース運用

---

## 5. Assumptions（前提）

- IRが `intent_type` を判定できる（少なくとも `OOS` / `QUESTION` / `SMALL_TALK` の判別が可能）
- DM内部で `dialogue_mode`（`SLOT_FILLING` / `STEP_BY_STEP`）を扱える
- 応答は必ず RP→RN→EG を通る（返答経路の統一）
- Mermaidレンダラは VSCode `bierner.markdown-mermaid` を前提とする（`["..."]` 運用）

---

## 6. Scope（対象範囲）

### In Scope（本設計パックで扱う）
- NLU/DM/NLGの責務分割
- DM内部（DST/DAE/DP）の分岐・合流設計
- LangGraph Stateの設計（キー/型/reducer、read/write）
- 例外処理の設計方針（retry/timeout/cancel/handoff）
- 評価指標・回帰試験の枠組み
- 運用（ログ/トレース/監視/Runbook）

### Out of Scope（本設計パックの範囲外）
- UI/フロント詳細
- IaCやクラスタ設計の詳細
- 全社データ基盤の網羅
- すべての業務ユースケースを網羅した台本（必要に応じてスライスで追加）

---

## 7. Minimal Glossary（最小用語）

- NLU / IR: 意図認識
- DM: 対話管理（DST/DAE/DPを含む）
- DST: 対話状態追跡（GST/SST）
- DAE: 行動実行（GE/SE）
- DP: 方針決定（GP/SFP）
- NLG: 応答生成（RP/RN）
- intent_type: `OOS` / `QUESTION` / `SMALL_TALK` / task intents…
- dialogue_mode: `SLOT_FILLING` / `STEP_BY_STEP`

> 詳細定義は `90_GLOSSARY.md` を正とする。

---

## 8. References（参照）
- ワークフロー図: `05_WORKFLOW_DM.md`
- State設計: `04_STATE_MODEL.md`
- ノード仕様: `06_NODE_SPECS.md`
