# 09_RUNBOOK - Dialogue System Design Pack
本章は運用手順書（Runbook）です。  
**本番運用で起きる障害の切り分け・一次対応・エスカレーション**を、誰でも迷わず実行できる形にまとめます。

> 方針：アジャイル前提で **最小→本番直前に厚く**する。  
> MVPでは「止血」と「原因特定」に必要な項目に絞る。

参照：
- 08_OBSERVABILITY.md（ログ/トレース/メトリクス/アラート）
- 07_TEST_PLAN.md（失敗系テスト、再現ケース）
- 04_NODE_CONTRACTS.md（ノード責務と失敗時挙動）
- 03_STATE_SPEC.md（Stateキーとログ抜粋）
- 13_SECURITY_AND_GUARDRAILS.md（PII/権限/監査）

---

## 0. Quick Actions（最初にやること：3分）
**目的：影響範囲を把握し、止血し、原因の当たりを付ける。**

1) **影響確認**
- いつから？（最初の異常検知時刻）
- どのチャネル？（Web/Teams/LINE）
- どのユースケース？（UC-01/02/03）
- どの割合？（error/fallback/handoffの急増）

2) **止血（安全側へ）**
- 外部ツールが原因なら：該当ツールを **disable**（Feature Flag / Config）
- LLMが原因なら：**縮退モード**（テンプレ応答＋handoff誘導）へ
- 重大な安全/PII疑いなら：**一時停止**（全体disable）＋セキュリティ連絡

3) **証跡確保**
- 代表 `session_id` を 3〜5件収集（成功/失敗混在）
- その `session_id` でログ・トレースを追跡
- 直近デプロイ（version/git_sha）と設定変更の有無を確認

---

## 1. On-call Checklist（オンコールの持ち物）
- アラートダッシュボード（error/fallback/tool timeout/latency）
- ログ検索（`session_id` / `node` / `tool_name` / `error_type`）
- 直近リリース一覧（version, change summary）
- Feature Flags / Config 変更手順
- エスカレーション連絡先（SRE/開発/セキュリティ/外部ベンダ）

---

## 2. Severity & Escalation（優先度とエスカレーション）
### SEV定義（例）
- **SEV-1**：PII漏洩疑い / 禁止領域出力 / 全面停止 / 大規模障害
- **SEV-2**：主要ユースケースが高頻度で失敗（例：error > 10%）
- **SEV-3**：部分劣化（特定ツールのみ、fallback増）
- **SEV-4**：軽微（単発、再現性低）

### エスカレーション基準
- SEV-1：即時（5分以内）にセキュリティ＋開発責任者
- SEV-2：15分以内に開発（必要なら外部API担当）
- SEV-3：当番が一次対応、改善チケット起票
- SEV-4：ログ記録のみ、定例でレビュー

---

## 3. Triage Flow（切り分けフロー）
```mermaid
flowchart TD
  A["Alert / User Report"] --> B{"SEV-1?<br/>PII/禁止領域/全面停止"}
  B -->|Yes| S1["Immediate Containment<br/>- Disable service/tool<br/>- Notify Security"]
  B -->|No| C{"Error or Latency spike?"}
  C -->|Error| D{"Dominant error_type?"}
  C -->|Latency| L{"Dominant node/tool?"}

  D -->|tool_timeout| T1["Check Tool Health<br/>KB/CRM/Ticket"]
  D -->|tool_4xx| T2["Auth/Permission/Token issue"]
  D -->|llm_error| M1["LLM Provider outage/limit"]
  D -->|state_inconsistent| I1["Bug suspected<br/>check recent deploy"]
  D -->|policy_violation| P1["Policy/config change?"]

  L -->|TOOL| T1
  L -->|LLM| M1
  L -->|NLG/DM| I1

  T1 --> Z["Mitigate: disable tool / raise timeout / fallback"]
  T2 --> Z
  M1 --> Z
  I1 --> R["Rollback / Hotfix"]
  P1 --> R
````

---

## 4. Where to Look（見る場所）

### 4.1 必須ログ（MVP）

検索キー：`session_id`, `turn_id`, `node`, `tool_name`, `error_type`, `outcome`, `version`

* Node span log（08の必須項目）
* 失敗例の `session_id` から IR→GST→…→NLG の順に追う
* `tool_status=error` がある場合は外部原因が濃厚

### 4.2 トレース（あれば）

* `trace_id` or `session_id` でスパンを連結
* どこで時間を食っているか（node/tool latency）

### 4.3 メトリクス（最小）

* `error_total{node,error_type}`
* `tool_call_total{tool_name,status}`
* `node_latency_ms{node}` / `tool_latency_ms{tool_name}`
* `fallback_total{node}` / `handoff_total{reason}`

---

## 5. Common Incidents（よくある障害と手順）

### 5.1 外部KBがtimeout（tool_timeout）

**Symptoms**

* `error_type=tool_timeout` 増加
* `tool_name=kb_search` の `tool_status=error` が急増
* fallback増加、UC-01が劣化

**Checks**

* KB APIのステータス/レート制限/SLA
* ネットワーク（DNS、VPC、TLS）変化
* 直近のtimeout/retry設定変更

**Mitigation（止血）**

* `kb_search` を一時disable → NLGで「現在検索できない」テンプレ＋handoff
* retry上限を下げ、全体遅延を抑える
* topKやクエリ長を下げる（負荷軽減）

**Recovery**

* KB復旧後に段階的にenable（カナリア）
* 影響期間のログをまとめてチケット化（外部担当へ）

---

### 5.2 CRMが403（tool_4xx / auth）

**Symptoms**

* `tool_status=error`, `error_type=tool_4xx`
* `tool_name=crm_lookup` が失敗
* handoff増える（本人確認必要等）

**Checks**

* トークン期限 / スコープ / 失効
* 権限ロール変更（最小権限の設定）
* IP許可リスト変更

**Mitigation**

* CRM参照を一時OFF（必要な場合は手動導線へ）
* 再認証誘導（ユーザー向け）または運用向け手順提示

**Recovery**

* 認証基盤/権限を復旧し、スモーク（TS-TOOL-001相当）で確認

---

### 5.3 LLMのエラー/レート制限（llm_error）

**Symptoms**

* `error_type=llm_error` 増加
* NLG/IR/GSTなど複数ノードで失敗
* 生成遅延が増える

**Checks**

* プロバイダのステータス
* レート制限 / quota / コスト上限
* 直近のプロンプト変更でトークン急増していないか

**Mitigation**

* 縮退モード：テンプレ応答＋handoff
* モデル切替（可能なら）／温度・max_tokens制限
* プロンプト短縮（緊急パッチ）

**Recovery**

* 復旧後に回帰（07のP0 golden）を回してから段階的に戻す

---

### 5.4 policyで拒否が増えた（policy_violation）

**Symptoms**

* `policy_disallowed=true` が急増
* refuse/handoffが増える
* 特定 intent で偏る

**Checks**

* 13のガードレール設定変更
* プロンプト変更で誤判定増加
* 入力側（チャネル）のスパム増加

**Mitigation**

* 直近変更をロールバック
* 誤検知の代表 `session_id` を収集し、ルール改善チケット化

---

### 5.5 state不整合（state_inconsistent）

**Symptoms**

* `error_type=state_inconsistent`
* 特定ノードで例外が連発
* 直近デプロイ直後に発生しやすい

**Checks**

* 03_STATE_SPEC と実装のズレ（キー名/型/enum）
* reducerの変更
* ノード間のR/W契約違反（04）

**Mitigation**

* 直近デプロイのロールバック
* 影響が限定なら該当フローを一時OFF

**Recovery**

* 該当ユースケースのgoldenテストを追加（再発防止）

---

## 6. Rollback / Hotfix（復旧手順）

### 6.1 ロールバック基準

* SEV-2以上で、原因が直近変更に強く紐づく場合
* 30分以内に解決見込みがない場合

### 6.2 ロールバック手順（例）

1. 現行 `version` を記録
2. 直前安定版に切替
3. P0 Golden（UC-01）を `MODE=stubbed` で実行
4. トラフィックを段階復旧（10%→50%→100%）
5. 事後：99に記録、原因チケット化

### 6.3 ホットフィックス手順（例）

* Feature Flag で回避できるならまずそれ
* 次に設定（timeout/topK/max_tokens）で回避
* 最後にコード修正（影響範囲が広いので慎重）

---

## 7. Post-Incident（事後対応）

### 7.1 必須アウトプット

* タイムライン（検知→止血→復旧）
* 根本原因（RCA）
* 再発防止（テスト追加、アラート追加、ADR更新）
* 影響（ユーザー数、期間、機能）

### 7.2 再発防止チェック

* 07_TEST_PLAN に失敗系を追加したか
* 08_OBSERVABILITY のアラート/メトリクスが不足していないか
* 03/04 の契約がズレていないか
* 99_DECISIONS_LOG に記録したか

---

## 8. Emergency Modes（緊急モード）

> 実装は Feature Flag / Config で提供する想定。

* `SAFE_MODE=on`：LLMを使わずテンプレ応答＋handoff
* `TOOL_KB=off`：KB検索停止（not foundテンプレ）
* `TOOL_CRM=off`：CRM参照停止
* `TICKET=off`：自動起票停止（手動導線）
* `STRICT_POLICY=on`：安全側に強める（誤拒否増に注意）

---

## 9. Contacts（連絡先）

* On-call（SRE）：@____
* 開発責任者：@____
* セキュリティ：@____
* 外部API（KB/CRM/Ticket）担当：@____

---

## 10. Open Items（本番直前に埋める）

* 具体的な閾値（error率、latency、timeout回数）
* Feature Flag の実装場所と切替手順（手順書リンク）
* 監査ログの保存先・閲覧権限
* 外部ベンダのSLAと連絡方法（夜間対応含む）
