# 02_BACKLOG - Dialogue System Design Pack
本章は、アジャイル開発のための **バックログ（Epic → Story）** を定義します。  
要求仕様（02_REQUIREMENTS.md 相当）を **“実装可能な単位”** に分割し、**Acceptance Criteria（AC）** と **優先度** を付与します。  
このバックログはスプリント計画の正（source of truth）であり、実装契約（04/06）と回帰テスト（15/11）にトレース可能であることを重視します。

---

## 0. Conventions（運用ルール）
- ID規約
  - Epic: `E-XX`
  - Story: `S-XXX`（Epicにぶら下げる）
- 優先度（MoSCoW）
  - **M**ust / **S**hould / **C**ould / **W**on’t（今はやらない）
- AC（Acceptance Criteria）
  - 原則 **Given/When/Then** で書く（検証可能な形）
- Trace（任意だが推奨）
  - `Touches State Keys`（触るStateキー）
  - `Touches Nodes`（触るノード）
  - `Tests`（15_TEST_PLAN.mdのケースID）

---

## 1. Epic一覧（俯瞰）
| Epic | Name | Goal | Priority |
|---|---|---|---|
| E-01 | MVP対話フロー（NLU→DM→NLG） | 最小の対話が成立する | M |
| E-02 | スロット充填（Clarify） | 不足情報を確認質問で埋める | M |
| E-03 | KB検索（FAQ/手順） | 根拠付き回答の土台 | M |
| E-04 | エラー処理・モード遷移 | retry/fallback/handoff | M |
| E-05 | 監査ログ・観測 | 運用可能な最低限 | M |
| E-06 | ツール連携（CRM/Ticket） | 条件付き参照・引き継ぎ | S |
| E-07 | プロンプト管理 | 変更影響を管理 | S |
| E-08 | 評価・回帰テスト | 変更で壊さない | S |
| E-09 | LLMOps/リリース | 変更を安全に出す | C |

---

## 2. Epic詳細（Stories）
> NOTE: 各Storyは「実装→テスト→観測」まで含めてDoneにする（DoDは00_VISION参照）。

---

### E-01 MVP対話フロー（NLU→DM→NLG）【M】
#### S-001 セッション開始・メッセージ受付
- **Priority**: M
- **Description**: チャネル入力を受け取り `session_id` 単位で処理を開始できる
- **AC**
  - Given 新規ユーザー入力  
    When APIが受領する  
    Then `session_id` が採番/取得され、グラフが起動される
  - Given 既存 `session_id` の入力  
    When APIが受領する  
    Then 既存Stateをロードして処理が継続される
- **Touches State Keys**: `session_id`, `messages`
- **Touches Nodes**: entrypoint（API層）
- **Tests**: TS-INT-001（session継続）

#### S-002 NLU（意図分類）の最小実装
- **Priority**: M
- **Description**: intent を `oos/question/procedure` 等に分類できる
- **AC**
  - Given 「住所変更したい」  
    When NLUが実行される  
    Then `intent_type="procedure"` がStateに格納される
  - Given 意図が不明確な入力  
    When NLUが実行される  
    Then `intent_type="oos"` または `question` として扱われ、非タスク経路に遷移できる
- **Touches State Keys**: `intent_type`, `messages`
- **Touches Nodes**: `IR`（Intent Recognition）
- **Tests**: TS-NLU-001（代表意図セット）

#### S-003 NLG（最小応答）を返せる
- **Priority**: M
- **Description**: 最小の応答を生成して返す（テンプレでも可）
- **AC**
  - Given intent_type が確定している  
    When 応答ノードが実行される  
    Then `response.message` が生成され返却される
- **Touches State Keys**: `response`
- **Touches Nodes**: `Response Nodes`
- **Tests**: TS-E2E-001（最小E2E）

---

### E-02 スロット充填（Clarify）【M】
#### S-010 スロットスキーマ定義（最小）
- **Priority**: M
- **Description**: 手続き系ユースケースに必要な最小スロットを定義する
- **AC**
  - Given `procedure_type="address_change"`  
    When スロット要件が評価される  
    Then 必須スロット（例：`contract_type`）が不足として列挙される
- **Touches State Keys**: `slots`, `missing_slots`
- **Touches Nodes**: `SST`（Slot-filling State Tracker）
- **Tests**: TS-SLOT-001（不足判定）

#### S-011 確認質問生成（1〜2項目）
- **Priority**: M
- **Description**: missing_slots を埋める質問を作る
- **AC**
  - Given `missing_slots=["contract_type"]`  
    When clarifyノードが実行される  
    Then 「契約種別（個人/法人）は？」のような質問が生成される
  - Given `missing_slots` が複数  
    When clarifyノードが実行される  
    Then 最大2項目までに絞って質問する（残りは次ターン）
- **Touches State Keys**: `clarifying_question`, `next_action`
- **Touches Nodes**: `SFP`（Slot-filling Policy）/ Clarify
- **Tests**: TS-SLOT-002（質問妥当性）

#### S-012 ユーザー回答でスロット更新
- **Priority**: M
- **Description**: ユーザー回答を反映して slots を更新する
- **AC**
  - Given 「個人です」  
    When intake/slot更新が走る  
    Then `slots.contract_type="personal"` がセットされる
  - Given スロットが全て埋まる  
    When 判定が走る  
    Then `missing_slots=[]` となり次アクションが `execute` に進む
- **Touches State Keys**: `slots`, `missing_slots`, `next_action`
- **Touches Nodes**: `SE`（Slot-filling Executor）/ Intake
- **Tests**: TS-SLOT-003（更新）

---

### E-03 KB検索（FAQ/手順）【M】
#### S-020 KB検索クエリ生成
- **Priority**: M
- **Description**: Stateを元に検索クエリを生成する
- **AC**
  - Given user_request と slots  
    When query生成  
    Then KBに投げる query が決まる（`kb.query`）
- **Touches State Keys**: `kb.query`
- **Touches Nodes**: Retrieve/Query Builder
- **Tests**: TS-KB-001（クエリ）

#### S-021 KB検索実行と結果格納
- **Priority**: M
- **Description**: KB APIを叩き topK をStateに格納する
- **AC**
  - Given query  
    When KB検索  
    Then `kb_hits` に上位K件が入る
  - Given 0件  
    When KB検索  
    Then `kb_hits=[]` で後続が適切に扱える
- **Touches State Keys**: `kb_hits`, `tool_trace`
- **Touches Nodes**: Retrieve/Search
- **Tests**: TS-KB-002（結果）

#### S-022 根拠付き回答生成
- **Priority**: M
- **Description**: KB結果を根拠として手順/FAQ回答を生成する
- **AC**
  - Given kb_hits が存在  
    When compose  
    Then 回答に根拠（記事ID/タイトル）が含まれる
  - Given kb_hits が空  
    When compose  
    Then 「見つからない」＋次の手段（質問/hand off）を提示する
- **Touches State Keys**: `final_answer`
- **Touches Nodes**: NLG/Compose
- **Tests**: TS-UC01（FAQ）, TS-UC02（手続き）

---

### E-04 エラー処理・モード遷移【M】
#### S-030 外部APIタイムアウト・リトライ
- **Priority**: M
- **Description**: KB/外部APIにタイムアウトとリトライ上限を実装
- **AC**
  - Given 外部APIがタイムアウト  
    When 実行  
    Then 最大N回リトライし、それでも失敗なら fallback に遷移する
- **Touches State Keys**: `last_error`, `next_action`, `tool_trace`
- **Touches Nodes**: Tool nodes / Error handler
- **Tests**: TS-FAIL-001（timeout）

#### S-031 fallback応答（安全縮退）
- **Priority**: M
- **Description**: 失敗時の安全な応答を返す
- **AC**
  - Given last_error がある  
    When fallback  
    Then できない理由＋次の手段（再試行/人手）を提示する
- **Touches State Keys**: `final_answer`
- **Touches Nodes**: Fallback
- **Tests**: TS-FAIL-002（fallback）

#### S-032 human handoff（条件と情報）
- **Priority**: M
- **Description**: 人手へ渡す条件と渡す情報を定義・実装
- **AC**
  - Given 解決不能 or policy で回答不可  
    When 判定  
    Then handoff に遷移し、必要情報（要約/スロット/ログ参照）を出力する
- **Touches State Keys**: `handoff_payload`
- **Touches Nodes**: Handoff
- **Tests**: TS-UC03（handoff）

---

### E-05 監査ログ・観測【M】
#### S-040 監査ログ（最小項目）
- **Priority**: M
- **Description**: セッション単位で処理経路を追跡できるログを出す
- **AC**
  - Given 1会話  
    When 実行  
    Then `session_id`, `node`, `mode`, `action`, `latency`, `outcome` が記録される
- **Touches State Keys**: `audit_ref`（任意）
- **Touches Nodes**: all nodes（log hook）
- **Tests**: TS-OBS-001（ログ項目）

#### S-041 メトリクス（最小）
- **Priority**: M
- **Description**: 成功率・エラー率・レイテンシを計測
- **AC**
  - Given 稼働  
    When メトリクス収集  
    Then success/error/latency が可視化できる
- **Touches State Keys**: なし（メトリクス基盤）
- **Touches Nodes**: Observability hook
- **Tests**: TS-OBS-002（メトリクス）

---

### E-06 ツール連携（CRM/Ticket）【S】
#### S-050 CRM参照（最小権限）
- **Priority**: S
- **Description**: 必要なときだけCRM参照を行う
- **AC**
  - Given customer_id があり許可されている  
    When CRM参照  
    Then 最小属性のみ取得される
- **Touches State Keys**: `crm_data`, `tool_trace`
- **Touches Nodes**: Tool/CRM
- **Tests**: TS-TOOL-001（CRM）

#### S-051 チケット起票（冪等）
- **Priority**: S
- **Description**: handoff時にチケットを起票する
- **AC**
  - Given handoff 判定  
    When ticket 実行  
    Then 冪等キーで二重起票が防止され、ticket_id が記録される
- **Touches State Keys**: `ticket_id`, `tool_trace`
- **Touches Nodes**: Tool/Ticket
- **Tests**: TS-TOOL-002（Ticket）

---

### E-07 プロンプト管理【S】
#### S-060 prompts/ の構成と変数規約
- **Priority**: S
- **Description**: プロンプトをファイル管理し、変数レンダリング規約を統一
- **AC**
  - Given prompts/ 配下  
    When 読み込み  
    Then 変数がレンダリングされ、プロンプト差分が追える
- **Touches State Keys**: なし（規約）
- **Touches Nodes**: LLM nodes
- **Tests**: TS-PROMPT-001（レンダリング）

---

### E-08 評価・回帰テスト【S】
#### S-070 回帰セット（固定データ）
- **Priority**: S
- **Description**: 代表ケースを固定し、モデル/プロンプト変更で比較できる
- **AC**
  - Given 回帰セット  
    When 実行  
    Then 成功率・ターン数などが比較できる
- **Touches State Keys**: なし
- **Touches Nodes**: Eval runner
- **Tests**: TS-EVAL-001（回帰）

---

## 3. Sprint Plan（例：MVP→拡張の順）
> 実際の計画はPMが更新。ここは例。

- Sprint 1（MVP成立）: S-001, S-002, S-003, S-010, S-011
- Sprint 2（解決まで）: S-012, S-020, S-021, S-022
- Sprint 3（運用最低限）: S-030, S-031, S-040, S-041
- Sprint 4（エスカレーション）: S-032, S-051
- Sprint 5（拡張）: S-050, S-060, S-070

---
