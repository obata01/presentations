# 09 Tools & Integrations - Dialogue System

本ドキュメントは、対話システムが利用する **外部ツール/API/DB** の統合方針を定義する。  
ワークフローは `05_WORKFLOW_DM.md`、Stateキーは `04_STATE_MODEL.md`、例外規約は `07_ERROR_HANDLING_AND_MODES.md` を正とする。

---

## 1. Scope（対象）
- 外部API（業務システム/CRM/検索/社内DB）
- RAG/検索（必要なら `10_DATA_AND_KB.md` と分担）
- 認証・認可（トークン、スコープ）
- タイムアウト、リトライ、冪等性、失敗時の返し方

---

## 2. Integration Principles（統合の原則）
- **ツール呼び出しは DAE（GE/SE）で行う**（推奨）
  - STEP_BY_STEP: GE が手順実行として tool_call する
  - SLOT_FILLING: SE が検証/照合/候補検索として tool_call する
- **結果はStateに“軽量に”保持**する（巨大レスポンスは参照IDへ）
- **失敗は分類して扱う**（user / external / internal / policy）
- **レスポンス経路は統一**：失敗しても最終的に `RP → RN → EG` で返す

---

## 3. Tool Interface（共通I/F）

### 3.1 Request（共通）
- `tool_name`: str
- `tool_args`: dict（必要最小限、PIIは最小化）
- `timeout_ms`: int（デフォルト値を決める）
- `idempotency_key`: str?（更新系は必須推奨）

### 3.2 Result（共通）
- `status`: `"ok" | "error"`
- `data`: dict（成功時。軽量に）
- `error`: dict（失敗時）
  - `type`: external / internal / policy
  - `code`: TIMEOUT / RATE_LIMIT / UNAUTHORIZED / NOT_FOUND / VALIDATION ...
  - `retryable`: bool

---

## 4. Timeouts / Retries（タイムアウト・リトライ）

- **timeout**：ツールごとに上限を設定（例：3〜10秒など）
- **retry**：`error.retryable==true` のみ許可
- **max_tool_retries**：初期値は `07_ERROR_HANDLING_AND_MODES.md` の推奨に従う（例：2回）

---

## 5. Idempotency（冪等性）
更新系（作成/変更/申請など）は原則：
- `idempotency_key` を付与
- 再試行しても二重実行にならない設計にする

---

## 6. Security / Privacy（認証・権限・PII）
- トークンは **最小権限**（read/write分離を推奨）
- PII（住所/氏名など）は
  - 送信：必要最小限
  - 保持：Stateに残しすぎない（ログはマスク）
- 監査/保持方針は `13_SECURITY_AND_GUARDRAILS.md` を正とする

---

## 7. Failure Handling（失敗時の方針）
- external（タイムアウト/5xx/レート制限）：
  - retry（上限まで）→ 超過で “今できない” 応答 or handoff
- user（入力不足/不正）：
  - SLOT_FILLING に戻す（可能なら）/ clarifying question
- internal（不整合/例外）：
  - safe fallback（固定テンプレ）＋ログ/アラート

> 具体の文面はRNテンプレ（`08_PROMPTS_AND_TEMPLATES.md`）で統一する。

---

## 8. Tool Catalog（カタログ：最小テンプレ）

ツールごとに以下を埋める（必要ツールだけ追記）。

### Tool: `<tool_name>`
- Purpose: （何をするか）
- Called by: `GE` / `SE`
- Inputs: （必要引数）
- Outputs: （返すデータの要点）
- Timeout: （ms）
- Retry: yes/no（条件）
- Idempotency: required/optional（更新系はrequired）
- PII: includes?（含むなら扱い方）
- Errors:
  - `TIMEOUT` (retryable)
  - `RATE_LIMIT` (retryable)
  - `UNAUTHORIZED` (not retryable)
  - `NOT_FOUND` (depends)

---

## 9. Open Questions（未決事項）
- tool_result を State に残す粒度（参照ID化のルール）
- 更新系ツールの冪等キー設計（どこで生成するか）
- ツール障害時の handoff 先（チケット/オペ連携）
