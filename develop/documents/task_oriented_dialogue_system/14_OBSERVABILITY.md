# 14 Observability - Dialogue System

本ドキュメントは、対話システムの **可観測性（ログ/トレース/メトリクス/アラート）** を定義する。  
セキュリティ/マスキングは `13_SECURITY_AND_GUARDRAILS.md`、評価指標は `11_EVALUATION_AND_METRICS.md` と整合させる。

---

## 1. Goals（目的）
- 1件の対話を「追える」（原因が特定できる）
- どこが遅い/壊れているかを「測れる」（SLO運用の土台）
- 回帰・劣化を「検知できる」（モデル/プロンプト変更の影響監視）
- PIIを漏らさずに観測する（マスキングを標準化）

---

## 2. Correlation IDs（相関ID）

全ログ/トレースで共通に持つ：
- `request_id`：リクエスト単位
- `session_id`：会話（スレッド）単位
- `turn_id`：ターン単位（1ユーザ発話＝1ターン）
- `user_id` / `tenant_id`：可能なら（匿名化可）

> これが揃うと「1ターンの全ノード」を追える。

---

## 3. Logging（ログ）

### 3.1 Log Levels（レベル）
- `INFO`：通常のターン進行、主要分岐、主要メトリクス
- `WARN`：リトライ、曖昧入力、フォールバック発生
- `ERROR`：ノード失敗、外部失敗上限超過、生成失敗
- `DEBUG`：開発環境のみ（PIIが混ざる可能性があるため本番は原則禁止）

### 3.2 Event Types（イベント種別）
- `turn.start`：SG通過
- `node.start` / `node.end`：ノード単位の開始/終了
- `route.decision`：intent_type/dialogue_mode/next_action の決定
- `tool.call` / `tool.result`
- `turn.end`：EG通過（レスポンス確定）

### 3.3 Required Fields（必須ログ項目）
最低限、以下を各イベントに入れる：

共通：
- `timestamp`
- `request_id`, `session_id`, `turn_id`
- `node`（例：IR/GST/SST/SE/GE/SFP/GP/RP/RN/NP）
- `workflow_revision`（グラフ定義版）
- `model_id` / `prompt_revision`（LLMを使うノードは必須）
- `latency_ms`（node.endで記録）

分岐（route.decision）：
- `intent_type`
- `dialogue_mode`
- `next_action`

State抜粋（PII配慮して最小）：
- `missing_slots`（スロット名のみ）
- `goal_step`（例：goal_state.current_step があれば）
- `error.type` / `error.code`（発生時）

### 3.4 Forbidden / Sensitive（原則ログに出さない）
- `slots` の値（住所、氏名など生PII）
- ユーザ発話の全文（必要なら短縮＋マスク、または参照ID化）
- KB本文の長い抜粋（doc_id/chunk_idのみ推奨）

> どうしても必要な場合は “サンプリング + マスク + 短縮” を徹底。

---

## 4. Tracing（分散トレース）

### 4.1 Trace unit（単位）
- 1ターン = 1 trace
- 各ノード = 1 span

推奨span構造：
- root span: `turn`
  - child spans: `SG`, `IR`, `GST`, `SST`, `SE`, `GE`, `SFP`, `GP`, `RP`, `RN`, `EG`
  - tool span: `tool/<tool_name>`（GE/SE配下）

### 4.2 Span attributes（span属性：推奨）
- `node`
- `latency_ms`
- `success` / `error`
- `intent_type`（IR後）
- `dialogue_mode`（GST後）
- `next_action`（SFP/GP/NP後）
- `retry_count`, `clarify_count`（あるなら）

---

## 5. Metrics（メトリクス）

### 5.1 System-level（システム全体）
- `requests_total`（総リクエスト）
- `turns_total`（総ターン）
- `errors_total{type}`（user/external/internal/policy）
- `latency_ms_p50/p95`（ターン全体）

### 5.2 Node-level（ノード単位）
- `node_latency_ms{node}` p50/p95
- `node_errors_total{node,type}`
- `node_retries_total{node}`（GE/SE/tool）

### 5.3 Dialogue quality（品質）
（定義は11を正とし、ここでは収集する前提を置く）
- `success_rate`
- `resolution_rate`
- `avg_turns`
- `reask_rate`
- `slot_completion_rate`
- `intent_routing_accuracy`（可能なら）

### 5.4 Tool-level（外部依存）
- `tool_calls_total{tool_name}`
- `tool_errors_total{tool_name,code}`
- `tool_latency_ms_p95{tool_name}`

---

## 6. Alerts（アラート）

### 6.1 Reliability（障害検知）
- エラー率上昇：
  - `errors_total{type="external"}` 急増
  - 特定ノードの `node_errors_total{node}` 急増
- タイムアウト増加：
  - `tool_errors_total{code="TIMEOUT"}` 急増
- 生成失敗：
  - `node_errors_total{node="RN"}` 急増

### 6.2 Performance（性能劣化）
- `turn_latency_p95` が閾値超過
- 特定ノード `node_latency_p95{node}` が閾値超過

### 6.3 Quality regression（品質劣化）
- `success_rate`/`resolution_rate` の急落
- `avg_turns`/`reask_rate` の急増
- `intent_type=OOS/QUESTION/SMALL_TALK` 比率の急変（誤ルーティングの兆候）

> 閾値は運用しながら `99_DECISIONS_LOG.md` で決める。

---

## 7. PII Masking（個人情報の扱い）

### 7.1 Masking rules（基本）
- ログに出す前にマスク（メール/電話/住所/番号など）
- スロットの値は “値” を出さず “スロット名のみ”
- KB参照は `doc_id/chunk_id` のみ（本文は最小限）

### 7.2 Environments（環境別）
- 本番：最小ログ（PIIなし）
- ステージング：必要最小で拡張可（ただし原則PIIなし）
- 開発：デバッグログは可だが、持ち出し禁止・期間限定・アクセス制限

---

## 8. Example Log Payload（例：node.end）

```json
{
  "timestamp": "2026-01-16T10:00:00+09:00",
  "level": "INFO",
  "event": "node.end",
  "request_id": "req-xxx",
  "session_id": "sess-xxx",
  "turn_id": "turn-003",
  "node": "GST",
  "workflow_revision": "wf-2026-01-16-a",
  "model_id": "model-x.y",
  "prompt_revision": "prompts-abc123",
  "latency_ms": 82,
  "intent_type": "task_address_change",
  "dialogue_mode": "SLOT_FILLING",
  "missing_slots": ["contract_type"]
}
````

---

## 9. Open Questions（未決事項）

* どの環境でどの粒度のログを許可するか（開発/検証/本番）
* user_textの保存方針（全文保存するか、要約/参照IDか）
* 品質指標（success/resolved）をオンラインでどう判定するか
* アラート閾値（p95、error rate）をどう設定するか

