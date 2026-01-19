# 15 Test Plan - Dialogue System

本ドキュメントは、対話システムのテスト方針（単体/統合/E2E）と、最低限のテストケース一覧を定義する。  
ワークフローは `05_WORKFLOW_DM.md`、例外規約は `07_ERROR_HANDLING_AND_MODES.md`、評価指標は `11_EVALUATION_AND_METRICS.md` を参照。

---

## 1. Goals（目的）
- 主要フロー（non-task / SLOT_FILLING / STEP_BY_STEP）が壊れていないことを保証する
- 例外系（timeout/retry超過/不整合）でも破綻しないことを保証する
- モデル/プロンプト変更時に回帰を検知できる仕組みを用意する

---

## 2. Test Levels（テストレベル）

### 2.1 Unit Tests（単体：ノード）
対象：
- IR, NP, GST, SST, SE, GE, SFP, GP, RP, RN, SG/EG（可能なら）

目的：
- 入力State → 出力State差分（Δ）が仕様通り
- パース不能時・不正入力時でも安全に扱える

### 2.2 Integration Tests（統合：フロー）
対象：
- `05_WORKFLOW_DM.md` の遷移が成立すること
- ノード間の契約（Stateキー/型）が噛み合っていること

### 2.3 E2E Tests（E2E：会話シナリオ）
対象：
- 複数ターンを跨ぐシナリオ
- 実運用に近い形（実モデル・実プロンプト・疑似ツール）

---

## 3. Test Data（テストデータ）

### 3.1 Golden Set（固定回帰セット）
- `11_EVALUATION_AND_METRICS.md` に準拠
- 代表フロー + 失敗系を含む
- 形式：JSONL 推奨（case_id, turns, expected）

### 3.2 Stubs / Mocks（外部依存）
- tool/APIは基本モック
- 失敗系（timeout, 5xx, rate_limit）を再現できるスタブを用意

---

## 4. Assertions（期待結果の型）

各テストで最低限確認する項目：
- ルーティング：`intent_type` / `dialogue_mode` / `next_action`
- 進行：期待するノード順（必要ならトレース/ログで確認）
- 状態：`missing_slots` の推移、`goal_state.current_step` の推移
- 応答：`response_plan.type` または RN の応答タイプ（answer/clarify/fallback 等）
- 例外：`error.type/code`、retry/clarifyカウント、上限超過時の収束

---

## 5. Test Cases（テストケース一覧：最小）

### 5.1 Unit Tests（ノード単体）

#### UT-IR-01：OOS判定
- Input：user_text が対象外要求
- Expect：`intent_type="OOS"` を出力、task系へ行かない

#### UT-IR-02：QUESTION判定
- Input：一般質問
- Expect：`intent_type="QUESTION"`

#### UT-IR-03：SMALL_TALK判定
- Input：雑談
- Expect：`intent_type="SMALL_TALK"`

#### UT-GST-01：SLOT_FILLING選択
- Input：task intent + 前提不足
- Expect：`dialogue_mode="SLOT_FILLING"`

#### UT-GST-02：STEP_BY_STEP選択
- Input：task intent + 前提十分
- Expect：`dialogue_mode="STEP_BY_STEP"`

#### UT-SST-01：missing_slots更新
- Input：entities/slotsの更新
- Expect：`missing_slots` が減る（または更新される）

#### UT-SE-01：slot正規化
- Input：slot候補（表記ゆれ）
- Expect：正規化済み `slots_delta` を返す

#### UT-SFP-01：確認質問生成
- Input：missing_slotsあり
- Expect：`next_action="clarify"`、`clarifying_question` セット

#### UT-GP-01：最終応答方針
- Input：実行完了相当のgoal_state
- Expect：`next_action="respond"`、`response_plan.type="answer"`（等）

#### UT-RN-01：clarify応答
- Input：response_plan.type=clarify + clarifying_question
- Expect：final_answer が質問文として生成される

#### UT-RN-02：fallback応答
- Input：error.type=internal
- Expect：安全応答テンプレにフォールバックする

---

### 5.2 Integration Tests（フロー）

#### IT-NT-01：OOSフロー
- Flow：SG → IR(OOS) → NP → RP → RN → EG
- Expect：
  - task系ノード（GST以降）を通らない
  - 応答が返る（fallback含む）

#### IT-NT-02：QUESTIONフロー
- Flow：SG → IR(QUESTION) → NP → RP → RN → EG
- Expect：解決または適切案内

#### IT-TASK-SF-01：SLOT_FILLINGフロー（1ターン）
- Flow：SG → IR(task) → GST(SF) → SST → SE → SFP → GP → RP → RN → EG
- Expect：
  - `dialogue_mode=SLOT_FILLING`
  - 応答が「確認質問」になり得る（missing_slotsに依存）

#### IT-TASK-SB-01：STEP_BY_STEPフロー（1ターン）
- Flow：SG → IR(task) → GST(SB) → GE → GP → RP → RN → EG
- Expect：
  - `dialogue_mode=STEP_BY_STEP`
  - 応答が「次ステップ/完了」になり得る

#### IT-JOIN-01：合流点の一貫性
- Case：NP経由とGP経由
- Expect：どちらも RP → RN → EG に合流する

---

### 5.3 E2E Tests（複数ターン）

#### E2E-SF-01：確認質問→回答→完了（SLOT_FILLING→STEP_BY_STEP）
- Turn1：前提不足のタスク要求
  - Expect：確認質問（missing_slots提示）
- Turn2：不足情報を回答
  - Expect：STEP_BY_STEPへ移行し、実行/完了応答

#### E2E-SB-01：手順進行（STEP_BY_STEP継続）
- 連続ターンで手順を進める
- Expect：goal_state.current_step が単調に進む（または想定通り遷移）

#### E2E-NP-01：質問→追加質問（non-task）
- Turn1：質問
- Turn2：追加質問
- Expect：NP経由で一貫した回答方針

---

## 6. Failure Tests（失敗系テスト）

### 6.1 Timeout（外部タイムアウト）
#### FT-TOOL-01：GEでtimeout→retry成功
- Setup：toolが1回timeout、2回目成功
- Expect：
  - retry_count が増える
  - 最終的に応答が返る

#### FT-TOOL-02：retry超過→handoff/安全応答
- Setup：toolが常にtimeout
- Expect：
  - max_tool_retries 超過
  - handoffまたは “今できない” 応答に収束

### 6.2 Clarify loop（確認質問のループ）
#### FT-CLARIFY-01：不足情報が埋まらない→上限で収束
- Setup：ユーザが無関係な返答を繰り返す
- Expect：
  - clarify_count が増える
  - max_clarify_turns 超過で handoff/終了に収束

### 6.3 Internal inconsistency（内部不整合）
#### FT-STATE-01：必要Stateキー欠損
- Setup：missing_slots未定義など
- Expect：
  - error.type=internal
  - RNがsafe fallback応答を返す（沈黙しない）

### 6.4 Misrouting（誤ルーティング）
#### FT-MODE-01：不足slotがあるのにSTEP_BY_STEPへ行った場合
- Setup：GST出力を意図的に誤らせる（または疑似）
- Expect：
  - 後段（GE/GP）で検知し、SLOT_FILLINGへ戻す or fallbackする

---

## 7. Test Execution（実行方法：運用）

### 7.1 When to run（いつ回すか）
- PR作成時：
  - 関連ノードのUnit + 最小Integration
- Release前：
  - Golden Set（回帰） + 代表E2E
- Model/Prompt変更：
  - Golden Set（必須） + 影響ノードのUnit（推奨）

### 7.2 Artifacts（成果物）
- 失敗した case_id / turn_id / node
- 差分（baseline vs candidate）の指標
- ログ/トレースのリンク（可能なら）

---

## 8. Open Questions（未決事項）
- Golden Set の保管場所と更新頻度
- E2Eをどの環境で回すか（stg/prod影響）
- success/resolved の自動判定方法（人手評価の併用範囲）
- 具体的な上限値（max_clarify_turns 等）の確定
