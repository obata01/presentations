# 08 Goal Definitions Schema - 目標定義書仕様

## 1. 概要

目標定義書（Goal Definitions）は、タスク指向対話システムにおける対話フローを宣言的に定義するYAML形式の設計書です。各ステップの遷移条件、応答生成ルール、スロットフィリング設定などを記述します。

---

## 2. ルートスキーマ

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `version` | string | ✓ | 定義書のバージョン（例: `"0.1"`） |
| `task_id` | string | ✓ | タスクの一意識別子（例: `"HEARING_FLOW"`） |
| `goal` | string | ✓ | タスクのゴール名（例: `"ヒアリング完了"`） |
| `description` | string | ✓ | タスクの説明文 |
| `steps` | Step[] | ✓ | ステップ定義のリスト |

---

## 3. Step スキーマ

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `id` | string | ✓ | ステップID（一意） |
| `name` | string | ✓ | ステップ名（表示用） |
| `desc` | string | | ステップの詳細説明 |
| `mode` | StepMode | ✓ | ステップの動作モード |
| `slot` | SlotConfig | | スロットフィリング設定（`mode: SLOT_FILLING` 時） |
| `action` | string | | 実行するアクション名（`mode: STEP_BY_STEP` 時） |
| `phase` | StepPhase | | 初期フェーズ |
| `response` | ResponseRule[] | ✓ | 応答生成ルールのリスト |
| `next` | Transition[] | ✓ | 遷移ルールのリスト |

---

## 4. 列挙型（Enums）

### 4.1 StepMode

| 値 | 説明 |
|----|------|
| `SLOT_FILLING` | スロットフィリングモード（情報収集） |
| `STEP_BY_STEP` | 逐次実行モード（アクション実行・確認） |

### 4.2 StepPhase

| 値 | 説明 |
|----|------|
| `NOT_STARTED` | 未開始 |
| `IN_PROGRESS` | 進行中 |
| `PENDING` | 確認待ち |
| `PROCESSED` | 処理完了 |
| `EXECUTION` | 実行中 |

---

## 5. SlotConfig スキーマ

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `name` | string | ✓ | スロットグループのクラス名 |
| `label` | string | ✓ | 表示用ラベル |

---

## 6. ResponseRule スキーマ

応答生成のルールを定義します。`if` 条件が true の場合に応答を生成します。

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `if` | Condition | | 条件式（省略時は常にマッチ） |
| `msg` | string | | 直接応答メッセージ（マルチライン可） |
| `via` | string | | 応答生成テンプレート/アクション名 |

> `msg` または `via` のいずれかを指定します。

### 6.1 Condition 記法

```yaml
if: { <context_key>.<field>: <value_or_list> }
```

- **単一値**: `{ current_slot_group_context.confirmed: false }`
- **複数値（OR）**: `{ current_slot_group_context.phase: [NOT_STARTED, IN_PROGRESS] }`

---

## 7. Transition スキーマ

ステップ間の遷移ルールを定義します。

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `at` | IntentType | ✓ | トリガーとなるインテント |
| `if` | Condition | | 追加の遷移条件 |
| `to` | string | ✓ | 遷移先ステップID |

### 7.1 IntentType（遷移トリガー）

| 値 | 説明 |
|----|------|
| `slot_inform` | スロット情報の提供 |
| `acknowledge` | 肯定・承諾 |
| `negation` | 否定・拒否 |
| `terminate` | 対話終了 |

---

## 8. サンプル

### 8.1 SLOT_FILLING モード（ヒアリング）
```yaml
version: 0.1
task_id: "HEARING_FLOW"
goal: "ヒアリング完了"
description: "ユーザの現職・職歴・希望条件をヒアリングします。"

steps:
  # ================================================================
  # 現職に関するヒアリング
  # ================================================================
  - id: current_job_hearing
    name: "現職に関するヒアリング"
    mode: SLOT_FILLING
    slot:
      name: CurrentJobHearingSlots
      label: "現職"
    phase: EXECUTION

    response:
      - if: { current_slot_group_context.confirmed: false }
        msg: |
          それでは現職に関するヒアリングを開始します。

          よろしいでしょうか！？
      - if: { current_slot_group_context.phase: [NOT_STARTED, IN_PROGRESS] }
        via: HEARING_NEXT_SLOT
      - if: { current_slot_group_context.phase: PROCESSED }
        via: SLOT_CONFIRM

    next:
      - at: slot_inform
        to: current_job_hearing
      - at: acknowledge
        if: { current_slot_group_context.phase: [NOT_STARTED, IN_PROGRESS, PENDING] }
        to: current_job_hearing
      - at: acknowledge
        if: { current_slot_group_context.phase: PROCESSED }
        to: past_job_hearing
        # to: hearing_completed
      - at: terminate
        to: hearing_end

```

### 8.2 STEP_BY_STEP モード（確認・アクション実行）
```yaml
version: 0.1
task_id: "HEARING_FLOW"
goal: "ヒアリング完了"
description: "ユーザの現職・職歴・希望条件をヒアリングします。"

steps:
  # ================================================================
  # 求人レコメンドと応募意思確認
  # ================================================================
  - id: job_recommend
    name: "求人レコメンドと応募意思確認"
    desc: "求人のレコメンドを実施して応募するかを確認する。"
    mode: STEP_BY_STEP
    action: JOB_RECOMMEND

    response:
      - via: JOB_RECOMMEND

    next:
      - at: acknowledge
        to: privacy_consent
      - at: negation
        to: next_recommend_confirm
      - at: terminate
        to: task_end

  # ================================================================
  # 個人情報の取り扱いへの承諾
  # ================================================================
  - id: privacy_consent
    name: "個人情報の取り扱いへの承諾"
    desc: "応募前に個人情報の取り扱いについての同意を頂きます。"
    mode: STEP_BY_STEP

    response:
      - msg: |
          応募にあたり、弊社の個人情報の取り扱いについて同意頂く必要がございます。
          以下の内容にご同意いただけますか？
          - 弊社はお預かりした個人情報を、以下の各号に定める目的の達成に必要な範囲内で、取得・利用いたし…
            (1)お客様からいただいたお問い合わせ・ご意見に対する回答
            (2)お客様ご本人の個人情報の利用目的の通知、開示、訂正・追加・削除又は利用の停止・消去・第三者…
          - なお、お預かりした個人情報は、上述各号の目的達成のために、必要な期間保有した後、速やかに適切…

    next:
      - at: acknowledge
        to: apply_process
      - at: negation
        to: next_recommend_confirm
      - at: terminate
        to: task_end

```
