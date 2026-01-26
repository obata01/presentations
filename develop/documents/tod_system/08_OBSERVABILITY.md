
# 08_OBSERVABILITY - Dialogue System Design Pack
本章は、対話システムの **観測（Observability）** を定義します。  
アジャイル前提で、まずは **最低限（MVP）** を確実に入れ、運用しながら **徐々に厚く**していきます。

- 目的：**再現・原因究明・品質改善・コスト管理**ができる状態にする
- 方針：State中心（03）・ノード中心（04）・ユースケース中心（05）で観測する
- 注意：PII/機密は必ずマスキング（詳細は 13_SECURITY_AND_GUARDRAILS.md）

---

## 1. Goals（観測のゴール）
### G1. Debuggability（原因究明）
- 「どのノードで」「何が起きて」「なぜ失敗したか」を `session_id` から追える

### G2. Reliability（信頼性）
- エラー率、タイムアウト、リトライ、fallback/handoff を定量化できる

### G3. Product Metrics（プロダクト品質）
- 解決率、平均ターン数、再質問率、スロット充填率などの改善指標が取れる

### G4. Cost & Performance（コスト・性能）
- LLMトークン、外部API回数、レイテンシを把握し、上限超えを検知できる

---

## 2. MVP Observability（最低限：これだけは必須）
> **MVPで必ず実装する観測**。07_TEST_PLAN.md で欠けていないことを検証する。

### 2.1 Log（構造化ログ：1行JSON推奨）
#### 必須フィールド（Node Span Log）
| Field | Type | Example | Notes |
|---|---|---|---|
| `ts` | string | `2026-01-19T12:34:56.789+09:00` | ISO8601 |
| `level` | string | `INFO` | ERROR/WARN/INFO |
| `env` | string | `dev/stg/prod` | |
| `service` | string | `dialogue-system` | |
| `version` | string | `git_sha` | リリース識別 |
| `session_id` | string | `sess_...` | 必須 |
| `turn_id` | string | `turn_0003` | 必須 |
| `node` | string | `IR` | 04と一致 |
| `action` | string | `classify_intent` | 任意だが推奨 |
| `dialogue_mode` | string | `SLOT_FILLING` | 07で遷移 |
| `intent_type` | string | `procedure` | |
| `outcome` | string | `success/fallback/handoff/error` | 必須 |
| `latency_ms` | int | `123` | 必須 |
| `retry_count` | int | `0` | toolのみでもOK |
| `error_type` | string | `timeout` | error時のみ |
| `tool_name` | string | `kb_search` | tool時のみ |
| `tool_status` | string | `success/error` | tool時のみ |
| `policy_disallowed` | bool | `false` | 必須 |
| `policy_pii_detected` | bool | `true/false` | 推奨 |

#### ログ例（Node Span）
```json
{"ts":"2026-01-19T12:34:56.789+09:00","level":"INFO","env":"prod","service":"dialogue-system","version":"a1b2c3d","session_id":"sess_golden_uc01_001","turn_id":"turn_0001","node":"TOOL","action":"kb_search","dialogue_mode":"STEP_BY_STEP","intent_type":"faq","outcome":"success","latency_ms":412,"retry_count":0,"tool_name":"kb_search","tool_status":"success","policy_disallowed":false,"policy_pii_detected":false}
````

### 2.2 Trace（分散トレーシング：最小）

* **Span単位**：`session_id` を trace_id か baggage として付与
* **Span名**：`node` をそのまま利用（IR/GST/.../TOOL/NLG）
* **必須属性**：`turn_id`, `intent_type`, `dialogue_mode`, `outcome`, `latency_ms`, `tool_name`（該当時）

> MVPでは「ログで追える」ことが最優先。Traceは後から厚くできる。

### 2.3 Metrics（メトリクス：最小）

#### カウンタ（Counter）

* `turn_total{env}`：ターン数
* `error_total{node,error_type}`：エラー数
* `fallback_total{node}`：fallback回数
* `handoff_total{reason}`：handoff回数
* `tool_call_total{tool_name,status}`：ツール呼び出し数

#### ヒストグラム（Histogram）

* `node_latency_ms{node}`：ノード遅延
* `turn_latency_ms`：ターン遅延（入口→出口）
* `tool_latency_ms{tool_name}`：ツール遅延

---

## 3. “State抜粋”ログ（安全なサマリ）

> State全文をログに出さない。**抜粋・要約・件数**のみ。

### 3.1 出して良い（例）

* `missing_slots_count`
* `messages_count`
* `citations_count`
* `plan_next_action`
* `tool_ref`（参照ID。PII含まない形式）

### 3.2 出してはいけない（例）

* ユーザー原文の全文（必要ならマスク済み短文のみ）
* CRMの生データ
* チケット本文の全文
* 住所/電話/メールなどのPII

---

## 4. Alerts（アラート：最小→拡張）

### 4.1 MVPアラート（必須）

* エラー率が閾値超え（例：5分平均で `error_total/turn_total > X%`）
* tool timeout 連続（例：`error_type=timeout` がY回/5分）
* turn_latency P95 超過（例：P95 > 3秒）

### 4.2 追加アラート（運用しながら）

* fallback急増（品質低下の兆候）
* handoff急増（UX悪化 or KB劣化）
* コスト急増（token/API回数の増加）
* 特定intentでの失敗偏り（回帰の兆候）

---

## 5. Dashboards（ダッシュボード：推奨）

### 5.1 MVPダッシュボード

* Overview

  * `turn_total`, `error_total`, `fallback_total`, `handoff_total`
  * `turn_latency_ms`（P50/P95）
* Tool

  * `tool_call_total`（status別）
  * `tool_latency_ms`（P95）
* Node

  * `node_latency_ms`（node別）
  * エラーTop（node×error_type）

### 5.2 品質ダッシュボード（後から）

* 解決率（self-serve）
* 平均ターン数
* 再質問率（clarify率）
* スロット充填率（missing_slotsの推移）

---

## 6. Correlation & IDs（相関ID設計）

### 6.1 必須ID

* `session_id`：会話単位の追跡キー（全ログ/トレース/メトリクスに紐付け）
* `turn_id`：ターン単位の追跡キー
* `request_id`：APIリクエスト単位（チャネル再送対策にも使う）

### 6.2 tool冪等キー（推奨）

* `idempotency_key = hash(session_id + turn_id + tool_name + tool_input_summary)`

---

## 7. Error Taxonomy（エラー分類：観測用）

> 07_ERROR_HANDLING_AND_MODES.md と整合すること。

* `user_input_invalid`：ユーザ起因（必要情報不足等）
* `policy_violation`：禁止/要注意
* `tool_timeout`：外部依存タイムアウト
* `tool_4xx`：認可/存在しない等
* `tool_5xx`：外部障害
* `llm_error`：モデル呼び出し失敗
* `state_inconsistent`：内部不整合（バグ疑い）

---

## 8. Privacy / Security Notes（必須）

* ログ・トレース・メトリクスには **PIIを含めない**（どうしても必要な場合はマスク/ハッシュ）
* `messages` は全文ログ禁止（必要なら要約＋マスク）
* tool出力全文ログ禁止（要約＋参照IDのみ）
* 監査用途の保存期間・アクセス権限は 13/16 に従う

---

## 9. Test Assertions（観測のテスト）

> 07_TEST_PLAN.md と連動。欠けたらCIで落とす。

* TS-OBS-001: 1ターン実行で必須ログ項目が欠けない
* TS-OBS-002: timeout/fallback時も `error_type` と `outcome` が記録される
* TS-OBS-003: PII文字列がログに含まれない（ルール検知）

---

## 10. Growth Plan（最低限→徐々に厚く）

### Phase 0（MVP）

* Node span log + 最小metrics + 最小alerts（本章2〜4）

### Phase 1（品質改善）

* 代表ユースケース別メトリクス（UC-01解決率、clarify率）
* 失敗理由の集計（handoff reasons）

### Phase 2（LLMOps連携）

* モデル/プロンプトバージョンと品質の差分可視化
* 回帰セットの自動採点（11）

---

## 11. Open Items（未決）

* 監査ログの保存先（DB/ログ基盤）と保持期間
* PII検知の方式（正規表現/DLP/LLM併用）と誤検知対策
* “解決率”の定義（何をもって解決とするか）
