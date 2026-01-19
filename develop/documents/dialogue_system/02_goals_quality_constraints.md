# Introduction & Goals / Constraints
対象：Dialogue System（LangGraph）

---

## 1. 目的（Goals）
- 問い合わせに対して、確認質問を挟みつつFAQ/手続き案内を完了させる
- 解決不能・高リスク時は人へエスカレーションし、チケット起票する

---

## 2. 成功指標（例）
- 自己解決率：>= 60%
- 平均応答時間：P95 < 3秒（外部API除く）
- チケット誤起票率：< 2%
- PII漏洩：0

---

## 3. 品質目標（Quality Goals）
- 安全性：禁止領域・PII・誤誘導を抑える
- 運用性：監査ログ、再現性、縮退がある
- 拡張性：ツール・ユースケース追加が容易
- 一貫性：同条件で同じルール・形式で応答

---

## 4. 制約（Constraints）
- Language：Python
- Orchestrator：LangGraph
- Persistence：Checkpoint Store（例：Postgres）
- 外部API：KB/CRM/Ticketはタイムアウト・レート制限・SLAあり
- セキュリティ：PIIマスキング、最小権限、監査ログ必須
