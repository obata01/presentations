# 00 Index - Dialogue System Design Pack

本ディレクトリは、LangGraphベースの対話システム（NLU → DM(DST/DAE/DP) → NLG）の設計・実装・評価・運用を一貫して扱うための「設計パッケージ」です。  
この 00 は “目次 + 読み方ガイド + 規約” をまとめた起点ページです。

---

## Quick Links (role-based)

### Implementer（実装担当）
- 04_STATE_MODEL.md
- 05_WORKFLOW_DM.md
- 06_NODE_SPECS.md
- 09_TOOLS_AND_INTEGRATIONS.md（外部連携がある場合）
- 14_OBSERVABILITY.md（ログ/トレースの実装）

### Reviewer / PM（仕様レビュー・要件確認）
- 01_CONTEXT_AND_SCOPE.md
- 02_REQUIREMENTS.md
- 03_ARCHITECTURE_OVERVIEW.md
- 05_WORKFLOW_DM.md

### Ops / SRE（運用・監視）
- 07_ERROR_HANDLING_AND_MODES.md
- 12_LLMOPS_AND_RELEASE.md
- 14_OBSERVABILITY.md
- 16_RUNBOOK.md
- 13_SECURITY_AND_GUARDRAILS.md（監査/権限が絡む場合）

---

## Folder Structure (recommended)

```
docs/
  00_INDEX.md
  01_CONTEXT_AND_SCOPE.md
  02_REQUIREMENTS.md
  03_ARCHITECTURE_OVERVIEW.md
  04_STATE_MODEL.md
  05_WORKFLOW_DM.md
  06_NODE_SPECS.md
  07_ERROR_HANDLING_AND_MODES.md
  08_PROMPTS_AND_TEMPLATES.md
  09_TOOLS_AND_INTEGRATIONS.md
  10_DATA_AND_KB.md
  11_EVALUATION_AND_METRICS.md
  12_LLMOPS_AND_RELEASE.md
  13_SECURITY_AND_GUARDRAILS.md
  14_OBSERVABILITY.md
  15_TEST_PLAN.md
  16_RUNBOOK.md
  90_GLOSSARY.md
```


---

## Documents (what & why)

### 01_CONTEXT_AND_SCOPE.md
- 何を作るか（ユースケース、ユーザ、成功条件、前提）
- 対象外と割り切り（Out of scope）
- 用語の最小セット（詳細は90へ）

### 02_REQUIREMENTS.md
- 機能要件：できること（例：住所変更手続き、求人提案、FAQ…）
- 非機能要件：速度、コスト、可用性、監査ログ、データ保持
- 制約：利用モデル、外部API、権限、個人情報

### 03_ARCHITECTURE_OVERVIEW.md
- “3枚構成” を推奨
  - 概観図（High-level）：層と主要コンポーネント、依存方向
  - コア図（Domain/Core）：重要な概念（Goal/Slot/Policy/Mode等）の関係
  - スライス図（Use-case slice）：特定ユースケースの詳細
- どこに何があるかの俯瞰を提供

### 04_STATE_MODEL.md
- LangGraph State の定義（キー、型、意味、初期値）
- reducer 方針（messagesはadd_messages等）
- 各ノードの read/write 一覧（表 or 図）
- 重要：Stateキーの命名規則、ログに出す項目

### 05_WORKFLOW_DM.md
- DMのワークフロー図（GST/SST/SFP/GP、分岐条件、合流）
- STEP_BY_STEP と SLOT_FILLING の統合仕様
- 例外遷移（fallback / retry / handoff）への接続点（概要）

### 06_NODE_SPECS.md
- ノードごとの仕様（NLU/GST/DAE/DP/NLG/TOOL 等）
  - 目的（責務）
  - 入力（読むState）
  - 出力（書くStateの差分 Δ）
  - 失敗時（例外・リトライ・fallback）
  - テスト観点（単体テストに必要な観点）
- 実装とレビューの “契約” になる資料

### 07_ERROR_HANDLING_AND_MODES.md
- 例外体系：分類（ユーザ起因/外部依存/内部不整合/ポリシー）
- retry上限、タイムアウト、キャンセル
- `dialogue_mode` の遷移ルール（必要ならステートマシン図を配置）
- human handoff（オペレータ連携）条件・情報

### 08_PROMPTS_AND_TEMPLATES.md
- プロンプト一覧（ファイル構成、変数、few-shot）
- バージョン管理（変更時の影響範囲）
- 禁止事項（リーク防止、ツール誤用防止のガード）

### 09_TOOLS_AND_INTEGRATIONS.md
- 外部ツール/API：I/F、タイムアウト、冪等性、失敗時の扱い
- 認証/認可（トークン、スコープ）
- tool_result / tool_error の State への格納方針

### 10_DATA_AND_KB.md
- KB/RAG を使う場合のデータ構造、更新・同期
- 参照範囲（権限、PII、マスキング）
- 取得失敗時の代替戦略

### 11_EVALUATION_AND_METRICS.md
- 成功率、平均ターン数、再質問率、スロット充填率、解決率
- 回帰テストセット（固定データ）
- モデル/プロンプト変更時の比較方法

### 12_LLMOPS_AND_RELEASE.md
- モデル切替・プロンプト変更の手順
- カナリア、A/B、ロールバック
- 変更が与える影響範囲（どのテストを回すか）

### 13_SECURITY_AND_GUARDRAILS.md
- 入力/出力の安全性、ポリシー、権限
- データ保持・削除、監査要件
- ツール呼び出し制約（許可リスト等）

### 14_OBSERVABILITY.md
- ログ項目（Stateの抜粋、mode、action、latency）
- トレース（ノード単位）
- メトリクス、アラート
- 個人情報の扱い（マスキング）

### 15_TEST_PLAN.md
- 単体（ノード）/統合（フロー）/E2E
- テストケース一覧、期待結果
- 失敗系（例外・タイムアウト・retry超過）のテスト

### 16_RUNBOOK.md
- 障害時の切り分け
- よくある失敗（外部API、認証、RAG欠損）
- 手動対応とエスカレーション

### 90_GLOSSARY.md
- 用語集（Goal/Slot/Mode/Policy/Stateなど）
- 略語辞書（NLU/DST/DAE/DP/NLG/DM）


### 99_DECISIONS_LOG.md
- 設計判断ログ（簡易ADR）
- 「何を選んだか / なぜ / 代替案 / 影響範囲」を短く残す



## Conventions（運用ルール）

### File naming@
- ファイル名は `NN_TITLE.md`（NNは2桁）で並び順を固定する

### Mermaid (bierner.markdown-mermaid)
- subgraphタイトル/ノードラベルは `["..."]` で囲う（パース安定化）
- ラベル中の改行は `<br/>` を使う
- 条件ラベルも `"..."` で囲う（記号混在に強い）

---

## Change Log
- 変更履歴・意思決定は `99_DECISIONS_LOG.md` を正とする
- 仕様変更（モード遷移、Stateキー、外部I/F、例外ルール）は必ず99に追記する
