# Cross-cutting Concepts（共通ルール）
対象：Dialogue System（LangGraph）

---

## 1. PII・セキュリティ
- messages / tool_trace / audit_log へ保存する前にマスキング
- CRM参照は最小権限（必要属性のみ）
- KB/CRM結果の“全文保存”は禁止。要約＋参照IDを原則

---

## 2. 監査ログ（Audit）
- 記録対象：ユーザー入力、モデル出力、ツール呼び出し（入力サマリ/結果サマリ/失敗理由）
- 相関ID：session_id / request_id を必須
- 禁止：PII生値、アクセストークン、秘密鍵

---

## 3. リトライ/タイムアウト/冪等性
- 外部API：timeout を固定（例：3s）＋最大リトライ（例：2回）
- Ticket起票：冪等キー（session_id + hash）で二重起票防止
- “空ヒット”は失敗ではない：composeで「見つからない」を明示

---

## 4. プロンプト規約
- system：安全・方針・禁止事項
- developer：出力フォーマット、参照すべきStateキー
- user：ユーザー入力＋最小限のコンテキストのみ

---

## 5. Checkpoint / TTL
- セッション再開のためにStateを保存（checkpoint）
- TTL：保持期間を明確化（例：30日）＋削除ジョブ
- 大きいデータはStateに入れない（要約して保持）
