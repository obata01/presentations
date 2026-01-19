# 90 Glossary - Dialogue System

本ドキュメントは、対話システム設計パックで使用する用語の定義と、略語辞書をまとめる。  
本ドキュメントは “用語の正” とし、各章から参照される。

---

## 1. Core Terms（主要用語）

### Goal（ゴール）
- 対話システムがユーザのために達成しようとする目的。
- 例：住所変更を完了する、求人提案の条件を確定する、申請を進める。

### Step / Step-by-step（ステップ／手順実行）
- Goal達成のための手順の単位。
- `STEP_BY_STEP` モードでは、手順の進行（次ステップ実行）が中心になる。

### Slot（スロット）
- タスク達成に必要な入力情報の枠。
- 例：契約種別、住所、希望勤務地、職種、希望年収など。

### Slot Filling（スロット充填）
- スロットを埋めるための対話・抽出・検証のプロセス。
- `SLOT_FILLING` モードでは、不足情報（missing_slots）を埋めることが中心になる。

### Mode（モード）
- 対話の進め方（フェーズ）を表す状態。
- 本設計では主に `dialogue_mode` を指す。
  - `SLOT_FILLING`
  - `STEP_BY_STEP`

> 例外処理などのために副モード（sub_mode/runtime_mode）を持つ場合がある（07参照）。

### Policy（ポリシー）
- 次に何をするか（質問する／実行する／返答する）を決める意思決定ロジック。
- 本設計では DP（Dialogue Policy）配下の SFP/GP が該当。

### State（ステート）
- LangGraphが保持する「会話の状態データ」。
- 例：messages、intent_type、dialogue_mode、slots、missing_slots、goal_state、next_action 等。

> 注意：UMLの「状態遷移図のstate（状態）」と、LangGraphのState（保持データ）は意味が異なる。

### Goal State（ゴール状態）
- ゴール進行を表す状態データ（例：current_step、progress）。
- `goal_state` としてStateに保持することが多い。

### Slot State（スロット状態）
- スロットの充足状況を表す状態データ。
- `slots`（値）と `missing_slots`（未充足）として保持することが多い。

### Entities（エンティティ）
- ユーザ発話から抽出された候補情報（人名/地名/日付/数値など）。
- slotへ投入する前の“素材”として扱うことが多い。

### Missing Slots（未充足スロット）
- タスク達成に必要だが、まだ埋まっていないスロット一覧。
- `missing_slots: list[str]` として保持し、質問戦略（SFP）やモード判定（GST）に利用する。

### Intent（意図）
- ユーザが何をしたいかの分類。
- 本設計では IR が `intent_type` を決定する。

### intent_type
- 意図分類のキー。
- 最低限 `OOS` / `QUESTION` / `SMALL_TALK` を区別し、タスク意図は別ラベル（task_xxx）にする想定。

### OOS（Out of Scope）
- 対象外要求。システムが直接は対応しない/できない要求。
- NP（Non-task Policy）で対応方針（案内/断り）を決める。

### QUESTION
- 一般質問・FAQ的問い合わせ。
- NPで回答方針を決め、RP→RNで応答する。

### SMALL_TALK
- 雑談・軽い会話。
- NPで対応方針を決め、RP→RNで応答する。

### Response Plan（応答方針）
- NLGに渡す構造化された応答設計（type、テンプレID、要点等）。
- `response_plan` としてStateに保持することが多い。

### Response Nodes（応答ノード）
- `response_plan` に基づいて最終応答文を生成するノード群。
- answer / clarify / fallback / refuse 等の分岐を持つことがある。

### Fallback（フォールバック）
- うまく処理できない場合に、破綻を避ける安全な応答へ落とすこと。
- 例：聞き返し、代替案提示、手動対応への誘導。

### Retry（リトライ）
- 外部API失敗などで再試行すること。
- 上限（max_tool_retries）を設けて無限化を防ぐ。

### Handoff（人手切替）
- 自動処理できない場合に、オペレータ/サポート等へ引き継ぐこと。

### Guardrails（ガードレール）
- 不適切出力・権限外実行・情報漏洩を防ぐ制御。
- 例：ツール許可リスト、PIIマスキング、拒否応答。

### Observability（可観測性）
- ログ/トレース/メトリクスでシステムを観測し、原因特定できる状態。
- 14で定義する。

### LLMOps（LLMOps）
- モデル/プロンプト/ルールの変更を安全にリリースし、品質を維持する運用。
- 12で定義する。

---

## 2. Abbreviation Dictionary（略語辞書）

### System Blocks
- **NLU**: Natural Language Understanding
- **DM**: Dialogue Manager
- **NLG**: Natural Language Generation

### NLU / Routing
- **IR**: Intent Recognition

### DM / State Tracking
- **DST**: Dialogue State Tracking
- **GST**: Goal State Tracking
- **SST**: Slot State Tracking

### DM / Execution
- **DAE**: Dialogue Act Executor
- **GE**: Goal Executor
- **SE**: Slot-filling Executor

### DM / Policy
- **DP**: Dialogue Policy
- **GP**: Goal Policy
- **SFP**: Slot-filling Policy

### NLG / Response
- **RP**: Response Proxy
- **RN**: Response Nodes
- **NP**: Non-task Policy

### Gates
- **SG**: Start Gate
- **EG**: End Gate

---

## 3. Document References（どこに書いてあるか）
- ワークフロー（正）: `05_WORKFLOW_DM.md`
- State設計（正）: `04_STATE_MODEL.md`
- 例外とモード: `07_ERROR_HANDLING_AND_MODES.md`
- LLMOps/リリース: `12_LLMOPS_AND_RELEASE.md`
- 可観測性: `14_OBSERVABILITY.md`
