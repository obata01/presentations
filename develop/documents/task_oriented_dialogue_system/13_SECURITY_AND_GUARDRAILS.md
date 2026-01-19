# 13 Security & Guardrails - Dialogue System

本ドキュメントは、対話システムにおける **安全性（入力/出力）**、**権限**、**データ保持/監査**、**ツール呼び出し制約**を定義する。  
例外規約は `07_ERROR_HANDLING_AND_MODES.md`、ツール統合は `09_TOOLS_AND_INTEGRATIONS.md` を参照。

---

## 1. Goals（目的）
- 機密/個人情報（PII）の漏洩や不適切出力を防ぐ
- 権限のない操作（ツール/API呼び出し）を防ぐ
- 監査可能性（誰が何を参照・実行したか）を担保する
- データ保持/削除（TTL、削除要求）を運用できる形にする

---

## 2. Threat Model（想定リスク：最小）
- **Prompt Injection**：ユーザ入力により、内部指示やツール実行を乗っ取られる
- **Data Leakage**：PII/機密情報が応答やログへ出る
- **Unauthorized Action**：権限外のツール呼び出し（更新系API、社内データ閲覧）
- **Over-retention**：不要な会話/データを長期保持してしまう
- **Insecure Logging**：ログにPIIや機密を出してしまう

---

## 3. Input Safety（入力の安全性）

### 3.1 Input classification（入力分類）
最低限以下を分類し、処理方針を切り替える：
- 通常入力
- 悪意ある指示（内部指示/ツール実行の強要）
- PII含有（住所・氏名・電話・メール等）
- 機密含有（社内限定情報、契約情報等）

### 3.2 Sanitization（サニタイズ）
- ログ出力前に PII をマスク（例：メール、電話、住所のパターン）
- 解析用に必要な場合でも、原文保存は最小化（参照ID化）

### 3.3 Injection defense（注入耐性）
- system promptで「ユーザの指示よりもシステム指示が優先」かつ「ツールは許可リストのみ」を明示
- ユーザ入力は “データ” として扱い、命令として扱わない（プロンプト構造で分離）
- retrieval（KB）の文章も同様に “データ” として扱う（引用文に従わない）

---

## 4. Output Safety（出力の安全性）

### 4.1 Output policy（出力ポリシー）
- PIIや機密を不要に復唱しない（slotsの値は最小限）
- 不確かな内容は断定しない（特にNP/FAQ）
- 禁止要求には拒否し、代替案を提示（必要ならhandoff）

### 4.2 Safe response（安全応答）
- 生成失敗/内部不整合/安全違反の疑いがある場合は **固定テンプレ**へフォールバック
- 最終経路は `RP → RN → EG` を維持し、沈黙しない

---

## 5. Authorization（権限・アクセス制御）

### 5.1 User context / identity（ユーザ識別）
- リクエストは `user_id / tenant_id / session_id` を持つこと（可能なら）
- KB参照やツール実行は、必ずユーザ属性（ロール/部署/契約種別等）に基づく

### 5.2 Least privilege（最小権限）
- ツール/APIは read/write を分離し、アプリからは必要最小限の権限のみ付与
- 秘密情報（APIキー等）は秘匿ストアで管理（コード/プロンプトに埋め込まない）

### 5.3 KB ACL（KBの参照権限）
- retrieval時点でACLフィルタ（許可された文書のみ検索/返却）
- 応答生成へ渡すコンテキストも同様に制限（多層防御）

> KBの詳細は `10_DATA_AND_KB.md`

---

## 6. Tool Guardrails（ツール呼び出し制約）

### 6.1 Allowlist（許可リスト：必須）
- `tool_name` は許可リストのものだけ実行可能
- さらに **ノードごとの許可リスト**を持つ（例：GEのみ更新系ツール可、SEは検索系のみ等）

### 6.2 Schema validation（引数検証）
- `tool_args` は schema（型/必須/範囲）で検証
- PIIを送る場合は明示（最小限、マスキング方針）

### 6.3 Human-in-the-loop（人手承認：任意）
更新系（取り消し不可、金銭、法務リスク等）の場合：
- 直前に確認（ユーザ確認）またはオペ承認を挟む
- 実行ログ（誰が、何を、いつ）を監査用に残す

---

## 7. Data Retention & Deletion（データ保持・削除）

### 7.1 Data categories（保持対象の分類）
- 会話ログ（messages）
- State（slots, goal_state, response_plan）
- tool_result / KB retrieved snippets
- 監査ログ（アクセス、実行）

### 7.2 Retention policy（保持期間：方針）
- 会話本文は短期（必要最小）を推奨
- 監査ログは要件に応じて別保持（改ざん耐性が必要な場合もある）
- PIIを含むデータは特に短期・最小化

> 具体的なTTL値は運用・法務要件により `99_DECISIONS_LOG.md` で確定する。

### 7.3 Deletion（削除）
- ユーザ/テナント単位で削除要求に応じられる設計
- 参照ID化している場合、参照先ストレージも含めて削除できること

---

## 8. Audit Requirements（監査要件）

最低限、以下を記録できること：
- 誰（user_id / tenant_id）が
- いつ（timestamp）
- どの処理（node / workflow_revision）
- どのデータにアクセス（KB doc_id/chunk_id、tool_name）
- どの実行を行ったか（tool_call、結果ステータス）

注意：
- 監査ログはPIIを最小化（値を残さず、参照IDと種類のみ）

---

## 9. Logging & Masking（ログとマスキング）

### 9.1 Must log（必須）
- `model_id`, `prompt_revision`, `workflow_revision`（12と整合）
- `intent_type`, `dialogue_mode`, `next_action`
- `error.type/code`, `at_node`
- tool: `tool_name`, status（引数/結果は最小）

### 9.2 Must NOT log（原則禁止）
- 住所・氏名などの生PII
- KBの本文の長い抜粋（必要なら短くマスクして）

> ログ詳細は `14_OBSERVABILITY.md` と整合。

---

## 10. Open Questions（未決事項）
- PII検知・マスキングの具体方式（ルール/モデル/ハイブリッド）
- 監査ログの保持期間と保存先（改ざん耐性の要否）
- toolの危険度分類（更新系の承認要否）
- 「ユーザ削除要求」への運用フロー（SLA、範囲）
