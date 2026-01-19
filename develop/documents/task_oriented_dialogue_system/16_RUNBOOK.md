# 16 Runbook - Dialogue System

本ドキュメントは、対話システムの運用・障害対応のための Runbook（手順書）である。  
可観測性は `14_OBSERVABILITY.md`、例外規約は `07_ERROR_HANDLING_AND_MODES.md`、セキュリティは `13_SECURITY_AND_GUARDRAILS.md` を参照。

---

## 1. What to do first（最初にやること）

### 1.1 Confirm scope（影響範囲確認）
- 影響は全体か？特定intentか？特定tenant/userか？
- いつから？（リリース直後か、外部障害タイミングか）

### 1.2 Find correlation IDs（相関IDを特定）
- `request_id` / `session_id` / `turn_id` を特定
- できれば対象ユーザ/セッションを再現できる形にする（PII注意）

### 1.3 Check dashboards（監視の確認）
- p95レイテンシ（turn, node）
- error rate（external/internal/policy）
- toolエラー（TIMEOUT/RATE_LIMIT/UNAUTHORIZED）
- RAG/KBエラー（retrieval 0件、permission denied）

---

## 2. Triage（切り分け：どこが壊れているか）

### 2.1 Symptom → likely area（症状別の当たり）
- 応答が返らない / 500：
  - アプリ例外、RN生成失敗、EGまで到達していない
- 遅い：
  - LLM遅延、外部API遅延、RAG検索遅延、リトライ増加
- `OOS` に偏る / taskに入らない：
  - IRのintent_type誤判定、プロンプト/モデル変更の影響
- スロットが埋まらない / 同じ質問を繰り返す：
  - SST/SE/SFPの不整合、missing_slots更新ミス、上限設定不足
- 手順が進まない：
  - GEの外部API失敗、前提不足の検知漏れ、goal_state更新ミス
- RAGが効かない：
  - retrieval 0件、インデックス同期遅延、ACLフィルタ過剰

### 2.2 Node-level check（ノード別チェック）
ログ/トレースで `node.end` を見て、失敗ノードを特定する。
- `IR`：intent_type / confidence
- `GST`：dialogue_mode
- `SST/SE`：missing_slots推移（スロット名のみ）
- `GE`：tool呼び出しの成否、retry_count
- `RN`：生成失敗/空出力

---

## 3. Common Incidents（よくある失敗と対応）

## 3.1 External API（外部API障害）

### Symptoms
- `error.type=external`
- `error.code=TIMEOUT` / `RATE_LIMIT` / `5XX`
- toolのp95レイテンシ上昇

### Checks
- tool別メトリクス：`tool_errors_total{tool_name,code}`
- 外部側ステータス（提供元の障害情報）
- リトライが増えていないか（retry_count）

### Mitigation（緩和策）
- カナリア/feature flagがあるならツール利用を停止（read-onlyに落とす等）
- retry上限を一時的に下げる（被害拡大防止）
- 代替手段（後で再試行/窓口案内）にRNテンプレを切替

### Escalation
- 外部提供元へ問い合わせ（時間帯・リクエスト量・request_id）
- 社内連携（SRE/基盤担当）へ障害共有

---

## 3.2 Auth / Permission（認証・権限）

### Symptoms
- `error.code=UNAUTHORIZED` / `FORBIDDEN`
- 特定tenant/userだけ失敗
- 直前に秘密情報/権限設定変更があった

### Checks
- トークン期限、ローテーション履歴
- スコープ（read/write）設定
- KB ACLフィルタの結果（permission deniedの増加）

### Mitigation
- 期限切れなら更新（運用手順に従う）
- 一時的に権限のある代替経路へ（handoff/案内）
- 影響が大きい場合はロールバック（12参照）

### Escalation
- セキュリティ/ID管理担当へ
- 監査が必要な場合は記録を残す（13参照）

---

## 3.3 RAG / KB Missing（RAG欠損・検索0件）

### Symptoms
- retrieval結果が常に0件
- 参照候補が出なくなった / 以前は出ていた
- 特定カテゴリだけ出ない

### Checks
- インデックス同期が止まっていないか（更新時間）
- ソース接続（権限/コネクタ）
- ACLフィルタが厳しすぎないか（restrictedが増えた等）

### Mitigation
- KBなしでも成立するfallback（追加質問/案内/FAQのみ）へ切替
- 同期を手動再実行（可能なら）
- 重要ソースのみを優先復旧（最小復旧）

### Escalation
- KB/検索基盤担当へ（doc_id, source, updated_at情報）
- 影響が全体なら障害宣言

---

## 3.4 Model / Prompt Regression（モデル/プロンプト回帰）

### Symptoms
- `intent_type=OOS` 比率が急増
- avg_turns / re-ask_rate が急増
- success_rate が急落
- RNの文体や禁則違反が増える

### Checks
- `model_id` / `prompt_revision` の変更有無（12参照）
- Golden Set の再実行（11参照）
- 影響ノード（IR/GST/SFP/GP/RN）のエラー増加

### Mitigation
- 直近リリースをロールバック（model_id/prompt_revision）
- カナリア停止、全体をbaselineへ戻す

### Escalation
- PM/実装責任者へ影響共有（case_id例、指標）
- 変更票/ADR（99）を更新

---

## 4. Manual Operations（手動対応）

### 4.1 Handoff（人手切替）
発生条件：
- retry上限超過
- clarify上限超過
- policy block / 権限不足

手動対応で渡す情報（PII注意）：
- `session_id`, `turn_id`
- intent_type, dialogue_mode
- missing_slots（名前のみ）
- error.type/code
- 必要なら、ユーザが何をしたいかの要約（マスク済み）

### 4.2 Temporary response switch（テンプレ切替）
- 外部API障害時： “現在実行できない” テンプレ
- KB障害時： “参照できないので追加情報をください” テンプレ
- 内部不整合時： safe fallback

> テンプレ運用は `08_PROMPTS_AND_TEMPLATES.md` と整合。

---

## 5. Escalation Policy（エスカレーション）

### 5.1 Severity（例）
- Sev1：全面停止、重大漏洩、法務/セキュリティ事故
- Sev2：主要機能が広範に失敗、外部API全面障害
- Sev3：特定intent/tenantで失敗、劣化（回帰）
- Sev4：軽微（単発、再現性低）

### 5.2 Who to contact（例）
- SRE/基盤：レイテンシ、5xx、インフラ
- アプリ担当：ノード例外、State不整合
- セキュリティ：権限、漏洩、監査
- KB担当：同期、検索、ACL
- PM：ユーザ影響、ロールバック判断

---

## 6. Post-incident（事後対応）
- 影響範囲、原因、再発防止策をまとめる（簡易ポストモーテム）
- `99_DECISIONS_LOG.md` に追記
- Golden Set に再発防止ケースを追加（11/15）

---

## 7. Quick Checklist（即応チェックリスト）
- [ ] request_id/session_id/turn_id を特定した
- [ ] 失敗ノード（IR/GST/SE/GE/RN等）を特定した
- [ ] error.type/code と retry/clarify超過の有無を確認した
- [ ] 直近リリース（model_id/prompt_revision）の変更を確認した
- [ ] 緩和策（feature flag/テンプレ切替/ロールバック）を実施または判断した
- [ ] 必要な相手にエスカレーションした
- [ ] 99へ記録する準備ができた
