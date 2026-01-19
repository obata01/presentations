# 02 Requirements - Dialogue System

本ドキュメントは、対話システムの要求事項（機能要件・非機能要件）と受入基準を定義する。  
背景・対象範囲は `01_CONTEXT_AND_SCOPE.md` を正とする。

---

## 1. Functional Requirements（機能要件）

### FR-01: Start Gate（入力受付）
- ユーザ入力を受け取り、ワークフローを開始できること

### FR-02: Intent Recognition（IR）
- `intent_type` を判定できること
- `intent_type in [OOS, QUESTION, SMALL_TALK]` を少なくとも判別できること

### FR-03: Non-task Policy（NP）
- `intent_type in [OOS, QUESTION, SMALL_TALK]` の場合、NPが応答方針を決定できること
- NPの出力は Response Proxy（RP）に渡されること

### FR-04: Task routing（IR→GST）
- `intent_type not in [OOS, QUESTION, SMALL_TALK]` の場合、GSTへ遷移できること

### FR-05: Goal State Tracking（GST）
- ゴール進行状態を更新できること
- `dialogue_mode` を扱い、次遷移を決定できること
  - `dialogue_mode==SLOT_FILLING` → SST
  - `dialogue_mode==STEP_BY_STEP` → GE

### FR-06: Slot State Tracking（SST）
- SLOT_FILLING のとき、スロット状態（例：slots/missing_slots）を更新できること
- SSTの後にSEへ遷移できること

### FR-07: Slot-filling Executor（SE）
- SLOT_FILLING のとき、抽出/正規化/検証/候補提示などの実行ができること
- SEの後にSFPへ遷移できること

### FR-08: Slot-filling Policy（SFP）
- 確認質問/追加質問/確定などの方針を決定できること
- SFPの後にGPへ合流できること

### FR-09: Goal Executor（GE）
- STEP_BY_STEP のとき、手順実行ができること
- GEの後にGPへ遷移できること

### FR-10: Goal Policy（GP）
- タスク系の最終方針（応答/次ステップ/必要情報）を決定できること
- GPの出力は Response Proxy（RP）に渡されること

### FR-11: Unified Response Path（RP→RN→EG）
- NP/GP いずれからも RP を経由して RN へ到達できること
- RN が応答文を生成できること
- EG を経由して最終レスポンスを返せること

### FR-12: State Management（LangGraph State）
- 各ノードが State を read/write できること
- 最低限、分岐と応答生成に必要なキーを保持できること
  - `messages` / `intent_type` / `dialogue_mode`
  - `slots` / `missing_slots`（SLOT_FILLING）
  - `goal_state`（STEP_BY_STEP）
  - `next_action` / `response_plan`（DP→NLG連携）

### FR-13: Exception handling（最低限）
- intent判定不能、外部失敗、矛盾入力などでも破綻しない応答が返せること
- 無限ループを防ぐ方針（上限や打ち切り）が定義されること  
  ※詳細は `07_ERROR_HANDLING_AND_MODES.md` に委譲

---

## 2. Non-Functional Requirements（非機能要件）

### NFR-01: Observability（可観測性）
- ノード単位でレイテンシ・成否が追えること
- 主要分岐（intent_type, dialogue_mode）がログに残ること

### NFR-02: Reliability（信頼性）
- 外部依存の失敗を想定し、リトライ/代替/打ち切りの方針があること
- 再質問や再実行が無限化しないこと

### NFR-03: Security & Privacy（セキュリティ/プライバシー）
- ログに個人情報が過剰に出ない（マスキング方針）
- 外部送信データは最小限であること

### NFR-04: Maintainability（保守性）
- intent/手順/スロット追加時に影響範囲が限定されること
- ドキュメント（04/05/06）が実装の契約として維持されること（99で記録）

### NFR-05: Testability（テスト容易性）
- ノード単体テスト（入力State→出力差分）が可能であること
- 代表フロー（OOS/QUESTION/SMALL_TALK、SLOT_FILLING、STEP_BY_STEP）の統合テストが可能であること

---

## 3. Acceptance Criteria（受入基準：最小セット）

1. `intent_type in [OOS, QUESTION, SMALL_TALK]` が NP 経由で応答できる  
2. `intent_type not in [OOS, QUESTION, SMALL_TALK]` が GST 起点で動作し、`dialogue_mode` により  
   - SLOT_FILLING: GST→SST→SE→SFP→GP  
   - STEP_BY_STEP: GST→GE→GP  
   のいずれも完走できる  
3. 最終応答は必ず RP→RN→EG を通って返る  
4. 主要分岐（intent_type / dialogue_mode）がログで追える  
5. 無限ループを防ぐ方針（上限/打ち切り/handoff）が定義される（詳細は07）

---

## 4. Constraints（制約）

- Mermaidは VSCode拡張 `bierner.markdown-mermaid` を前提とし、ラベルは `["..."]` を推奨
- ワークフロー図は `05_WORKFLOW_DM.md` を正とする
- State/ノード仕様は `04_STATE_MODEL.md` / `06_NODE_SPECS.md` を正とする

---

## 5. Open Questions（未決事項：要求として残す）

- intent_type の分類体系（task intents の一覧、粒度）
- `dialogue_mode` の決定責務（GST固定か、ルータ層か）
- スロットのスキーマ（slots/missing_slots の型・検証）
- 外部実行（ツール/API）をどのノードが担うか（GE/SE/別TOOLノード）
- retry/timeout/handoff の具体値（上限回数、タイムアウト秒）
- ログに残すState項目とマスキング方針

> 未決事項・合意事項は `99_DECISIONS_LOG.md` に記録する。
