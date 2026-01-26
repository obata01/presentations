# 12 LLMOps & Release - Dialogue System

本ドキュメントは、対話システムにおける **モデル切替**・**プロンプト変更**・**ルール変更**のリリース手順を定義する。  
評価指標は `11_EVALUATION_AND_METRICS.md`、テスト計画は `15_TEST_PLAN.md`、例外規約は `07_ERROR_HANDLING_AND_MODES.md` を参照。

---

- 自動でテスト、という自動はどこまで自動？
- プロンプト管理やバージョン管理
- ユーザやThreadID別のトークン数やコストをログに出す（Stateに入れる？）
- エージェントに関してはLLM-as-a-Judgeも検討
- レイテンシーチェック
- フォールバック（OpenAIが落ちたらClaudeへ、など予備回線の設定）


## 1. Goals（目的）
- 変更（モデル/プロンプト/ルール）が品質へ与える影響を可視化し、事故なくリリースする
- 回帰を検知し、即座にロールバックできる状態を作る
- 変更の「影響範囲」と「回すべきテスト」を標準化する

---

## 2. Change Types（変更種別）

- **Model change**：モデルバージョン/プロバイダ切替、推論パラメータ変更
- **Prompt change**：system/user prompt、few-shot、テンプレ変更など
- **Routing/Rule change**：intent_type分類、dialogue_mode判定、next_actionルール
- **Tool/Integration change**：外部API I/F、タイムアウト、冪等性、権限
- **KB/Data change**：インデックス更新、チャンク方針、検索/再ランキング設定

---

## 3. Versioning & Traceability（版管理と追跡）

### 3.1 Required metadata（必須）
各リクエスト/セッションに以下をログとして残す：
- `model_id`（例：provider + version）
- `prompt_revision`（プロンプトのgit hash / version）
- `workflow_revision`（グラフ定義のバージョン）
- `config_revision`（閾値や上限値）
- `kb_revision`（KB/RAGを使う場合）

> ログ要件は `14_OBSERVABILITY.md` と整合する。

---

## 4. Release Pipeline（標準リリース手順）

### Step 0: Change ticket（変更票）
- 変更内容、目的、影響ノード、対象環境（dev/stg/prod）
- 失敗時のロールバック方法（必須）

### Step 1: Offline regression（オフライン回帰）

`Golden Set`（固定データ）で変更前後の差分を評価する。評価は以下の2レベルで実施：

#### 1.1 システムレベル評価（シナリオテスト）
- **Task Success Rate（タスク達成率）**: シナリオが正常完了した割合
- **Response Accuracy（応答正解率）**: 最終発話や提示情報が期待内容（必須キーワード）と一致した割合
- 壊れた `case_id` と原因分類（IR/mode/slot/exec/policy/NLG）を出す

#### 1.2 モジュールレベル評価
- **Intent Accuracy（意図判定正解率）**: `intent_type` が正解ラベルと一致した割合。特に `OOS`/`SMALL_TALK` の誤判定を監視
- **Slot F1 Score**: スロット抽出の適合率(Precision)と再現率(Recall)の調和平均。抽出漏れと過剰抽出の両方を評価

> 詳細は `11_EVALUATION_AND_METRICS.md` を参照

### Step 2: Staging validation（ステージング検証）
- 代表シナリオのE2E（task/non-task、SLOT_FILLING/STEP_BY_STEP）
- 外部ツールがある場合は疑似/サンドボックスで確認

### Step 3: Canary（カナリア）
- 本番トラフィックの一部（例：1%→5%→20%）に段階投入
- 主要指標（成功率、解決率、平均ターン、再質問率、エラー率）を監視
- 異常時は即時停止・ロールバック

### Step 4: A/B（必要な場合）
- Candidate/Baseline を同時運用し、セグメント別に比較
- 有意差・悪化ケース・安全性（禁則違反）を確認

### Step 5: Full rollout（全面展開）
- ロールアウト完了を宣言
- 事後レビュー（ポストモーテム/学び）を記録

---

## 5. Canary / A-B / Rollback（運用詳細）

### 5.1 Canary（カナリア）
- 入口でルーティング（ユーザIDハッシュ、セッションIDで固定割当）
- 監視項目（最低限）
  - **Task Success Rate（タスク達成率）**
  - **Intent Accuracy（意図判定正解率）**
  - **Slot F1 Score**
  - error rate（external/internal/policy）
  - latency（p50/p95）
- 停止条件（例）
  - success率がX%低下、またはエラー率がY%上昇
  - 禁則違反が発生（セキュリティ/PII等）

### 5.2 A/B（A/Bテスト）
- 比較期間は短すぎない（季節性・曜日影響を避ける）
- 同じユーザは同じバリアントに固定（学習効果によるブレを減らす）
- **オンライン評価指標**：
  - システムレベル指標（Task Success Rate, Intent Accuracy等）
  - **ユーザフィードバック（主観評価）**: アンケートによるユーザ満足度測定（詳細は `11_EVALUATION_AND_METRICS.md`）

### 5.3 Rollback（ロールバック）
- ロールバック対象：
  - model_id を戻す
  - prompt_revision を戻す
  - workflow_revision / config_revision を戻す
- ロールバック手順：
  - 「即時」切替できるようにフラグ/設定で管理（デプロイ不要が理想）
- ロールバック後：
  - Golden Set 再実行 → 直前状態に戻ったことを確認
  - 99に事象を記録

---

## 6. Test Matrix（変更種別→回すべきテスト）

| Change Type | Must run（必須） | Recommended（推奨） |
|---|---|---|
| Model change | Golden Set（11）+ E2E代表（15） | カナリア（本番） |
| Prompt change | Golden Set（11）+ 対象ノード単体（15） | カナリア / A/B |
| Routing/Rule change | 分岐テスト（intent/mode）+ Golden Set | ステージングE2E |
| Tool/Integration change | ツール結合テスト + 失敗系（timeout/retry） | カナリア（エラー率監視） |
| KB/Data change | KB系Golden（検索/引用）+ 禁則チェック | A/B（必要なら） |

---

## 7. Safety & Compliance checks（安全チェック）
- PII/機密の漏洩がないこと（ログ/応答）
- 禁止事項応答がないこと（policy）
- ツール呼び出し制約が守られること

> 詳細は `13_SECURITY_AND_GUARDRAILS.md`

---

## 8. Release Checklist（最小チェックリスト）
- [ ] 変更票がある（目的/影響/ロールバック）
- [ ] Golden Set の差分が許容範囲
- [ ] 代表E2Eが通る（task/non-task、2モード）
- [ ] ログに model_id / prompt_revision が残る
- [ ] カナリアの停止条件が定義されている
- [ ] ロールバック手順が実行可能（切替確認済み）

---

## 9. Open Questions（未決事項）
- 停止条件（X%, Y%）の具体値
- カナリアの段階（1%→5%→20%→100%等）
- A/Bの実施条件（どの変更なら必須か）
- 変更の承認フロー（誰がGo/No-Goを出すか）
