# 08 Prompts & Templates - Dialogue System

本ドキュメントは、対話システムで使用する **プロンプト（LLM指示）** と **テンプレート（応答/構造）** を管理するためのルールと一覧を定義する。  
ワークフローは `05_WORKFLOW_DM.md`、Stateキーは `04_STATE_MODEL.md`、ノード仕様は `06_NODE_SPECS.md` を正とする。

---

## 1. Goals（目的）
- プロンプト変更が「どこに効くか」を明確にし、改修を安全にする
- ノード単位でプロンプトを管理し、責務を分離する
- 回帰（品質低下）の原因を特定しやすくする（版管理・評価と連動）

---

## 2. Scope（対象）
- LLMを用いるノード（例：IR, GST, SST/SE, GE, SFP, GP, RN, NP）
- ルールベースで十分な箇所は “テンプレ/関数” で管理し、LLM依存を最小化する
- このドキュメントは「ファイル配置」「変数」「出力形式」「運用ルール」を扱う

---

## 3. Recommended Folder Layout（推奨フォルダ構成）

```

prompts/
system/
base_system.md
nlu/
ir.md
dm/
gst.md
sst.md
se.md
ge.md
sfp.md
gp.md
nlg/
rp.md
rn_answer.md
rn_clarify.md
rn_refuse.md
rn_fallback.md
non_task/
np.md
templates/
response/
clarify.md
apology_short.md
cannot_do.md
handoff.md
schema/
intent_type.json
dialogue_mode.json
response_plan.json

```

> 「prompts = LLMに渡す文章」「templates = 人間が読める定型文/構造」を分ける。

---

## 4. Prompt Contracts（プロンプトの契約）

### 4.1 Common variables（共通変数）
以下は全プロンプトで利用可能（推奨）とする。

- `messages`: 会話履歴（必要なら直近N件に制限）
- `user_text`: 最新ユーザ発話
- `intent_type`
- `dialogue_mode`
- `goal_state`
- `slots`, `missing_slots`
- `error`（直近の失敗情報）

### 4.2 Output format policy（出力形式）
- 可能な限り **JSON** で返させる（ノード間の契約を固める）
- 文字列応答（自然文）は RN（Response Nodes）に集約する
- JSONには **必須キー** と **許可キー** を明示し、パース失敗時のfallbackを定義する

推奨：
- IR: `{ "intent_type": "...", "confidence": 0.0-1.0, "entities": {...} }`
- GST: `{ "dialogue_mode": "...", "goal_state": {...} }`
- SFP/GP: `{ "next_action": "...", "response_plan": {...}, "clarifying_question": "..."? }`
- RN: `{ "final_answer": "..." }`（または純テキストでも可）

### 4.3 Guardrails（禁止事項）
- 未許可のツール呼び出しを提案しない／しない
- 個人情報をむやみに復唱しない（slotsの値をそのままログや応答に出さない設計）
- “確信がない推測” を断定しない（特にNP/FAQ系）

---

## 5. System Prompt（共通システム指示）

`prompts/system/base_system.md`（例）
- 役割（対話システムの一部として、指定の形式で出力する）
- 安全規約
- 出力形式（JSON、キー制限）
- 不明時の振る舞い（confidence低いときはclarify等）

> 実装上は system prompt を全ノード共通にし、ノード固有の指示は user prompt 側へ分離するのが推奨。

---

## 6. Node Prompt List（ノード別プロンプト一覧）

### 6.1 NLU

#### IR（Intent Recognition）
- File: `prompts/nlu/ir.md`
- Goal: `intent_type` 判定、entities抽出（必要最小）
- Output: JSON（intent_type, confidence, entities）

---

### 6.2 DM / DST

#### GST（Goal State Tracking）
- File: `prompts/dm/gst.md`
- Goal: goal_state更新、dialogue_mode決定（SLOT_FILLING/STEP_BY_STEP）
- Output: JSON（dialogue_mode, goal_state, rationale?）

#### SST（Slot State Tracking）
- File: `prompts/dm/sst.md`
- Goal: slots/missing_slots更新（追跡）
- Output: JSON（slots_delta, missing_slots）

---

### 6.3 DM / DAE

#### SE（Slot-filling Executor）
- File: `prompts/dm/se.md`
- Goal: 抽出・正規化・検証・候補生成（slot処理の実行）
- Output: JSON（slots_delta, missing_slots, validation_errors?）

#### GE（Goal Executor）
- File: `prompts/dm/ge.md`
- Goal: 次ステップ実行（手順の進行）
- Output: JSON（goal_state_delta, tool_request?）

> tool呼び出しがある場合、tool_requestを別の実行層へ渡す（詳細は09/06）

---

### 6.4 DM / DP

#### SFP（Slot-filling Policy）
- File: `prompts/dm/sfp.md`
- Goal: 確認質問の方針、質問文候補、次行動決定
- Output: JSON（next_action, clarifying_question?, response_plan）

#### GP（Goal Policy）
- File: `prompts/dm/gp.md`
- Goal: タスク全体の応答方針・次ステップ・終了判定
- Output: JSON（next_action, response_plan）

---

### 6.5 Non-task

#### NP（Non-task Policy）
- File: `prompts/non_task/np.md`
- Goal: OOS/QUESTION/SMALL_TALK の応答方針
- Output: JSON（response_plan）

---

### 6.6 NLG

#### RP（Response Proxy）
- File: `prompts/nlg/rp.md`（LLMでやる場合のみ）
- Goal: response_planに基づいて RN を選択（テンプレ中心ならLLM不要）

#### RN（Response Nodes）
- Files:
  - `prompts/nlg/rn_answer.md`
  - `prompts/nlg/rn_clarify.md`
  - `prompts/nlg/rn_refuse.md`
  - `prompts/nlg/rn_fallback.md`
- Goal: 最終応答テキスト生成（またはテンプレ適用）
- Output: `final_answer`（テキスト）

---

## 7. Response Plan Schema（推奨）

`templates/schema/response_plan.json` の想定例（概念）

- `type`: `"answer" | "clarify" | "refuse" | "fallback" | "handoff"`
- `template_id`: 例 `"clarify.missing_slots.v1"`
- `summary`: ユーザに伝える要点（箇条書き）
- `tone`: `"polite" | "neutral" | "friendly"`
- `data`: RNに渡す構造化データ（missing_slots等）

> response_plan の “正” は `04_STATE_MODEL.md` と整合させる。

---

## 8. Templates（テンプレート）

テンプレは RN（またはNLG層）で利用する。

### 8.1 Clarify templates
- `templates/response/clarify.md`
- 目的：不足情報（missing_slots）を短く聞く

### 8.2 Fallback templates
- `templates/response/apology_short.md`
- `templates/response/cannot_do.md`
- 目的：内部不整合や対象外の安全応答

### 8.3 Handoff templates
- `templates/response/handoff.md`
- 目的：人手切替時の説明と引き継ぎ情報の提示

---

## 9. Versioning（版管理）

### 9.1 Naming
- ファイルは原則 `snake_case.md`
- テンプレ/planには `v1/v2` を付ける（破壊的変更を避ける）

### 9.2 Change logging
- プロンプト変更は必ず `99_DECISIONS_LOG.md` に記録
  - 変更理由
  - 影響ノード
  - 回帰テスト範囲（11/15のどれを回すか）

### 9.3 Rollback
- リリース手順は `12_LLMOPS_AND_RELEASE.md` を正とする
- “prompt only” 変更でも回帰テストを行う

---

## 10. Prompt Writing Rules（書き方のルール）

- 1プロンプト = 1責務（IRに手順実行をさせない等）
- 出力形式（JSONキー）を明示し、許可キー以外を出させない
- 失敗時の挙動を明示（confidence低→clarify、パース不能→fallback）
- 長文履歴は要約/直近N件に制限（messages肥大化を防ぐ）

---

## 11. Open Questions（未決事項）
- entity抽出を IR で固定するか、SE（DAE側）に寄せるか（現状：entity抽出はDAEで実行方針）
- response_plan の正式スキーマ（最小キー、テンプレID体系）
- RNをテンプレ中心にするか、LLM生成中心にするか
- tool_request（GE/SE）をどの形式で表すか（09と整合）

> 決定事項は `99_DECISIONS_LOG.md` に記録する。



