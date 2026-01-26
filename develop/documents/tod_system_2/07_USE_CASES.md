
対話シナリオに沿って、各ノードで各State変数をどう変更するかを示す。

## サンプル対話シナリオ: 面談

### シナリオ
- AI：「どちらにしますか？①面談したい ②手続きしたい」
- User：「面談したい」
- AI：「それでは現職についてヒアリングを開始してよろしいですか？」
- User：「はい」
- AI：「現職の会社名を教えてください。」
- User：「株式会社○○です。」
- AI：「現在の職種を教えてください。」
- User：「営業です。」
- AI：「ヒアリングは以上です。」


### シーケンス図.

```mermaid
sequenceDiagram
  autonumber
  actor U as User
  participant INV as graph.invoke()
  participant SG as SG<br/>(Start Gate)
  participant IR as IR<br/>(Intent Recognition)
  participant GST as GST<br/>(Goal State Tracker)
  participant SST as SST<br/>(Slot State Tracker)
  participant SE as SE<br/>(Slot-filling Executor)
  participant SP as SP<br/>(Slot-filling Policy)
  participant GE as GE<br/>(Goal Executor)
  participant GP as GP<br/>(Goal Policy)
  participant RN as RN<br/>(Response Nodes)
  participant EG as EG<br/>(End Gate)

  %% === ターン1: ゴール選択の提示（初期状態） ===
  Note over U, EG: ターン1: 初期メニュー提示
  Note right of RN: Δ response="どちらにしますか？①面談したい ②手続きしたい"
  RN->>EG: 応答生成完了
  Note right of EG: Δ chat_history+=AI("どちらにしますか？...")
  EG-->>U: 「どちらにしますか？①面談したい ②手続きしたい」

  %% === ターン2: ユーザーが「面談したい」を選択 ===

  Note over U, EG: ターン2: ゴール選択「面談したい」
  U->>INV: 「面談したい」
  Note right of INV: Δ query="面談したい"
  Note right of INV: Δ thread_id="session_001"

  INV->>SG: グラフ実行開始
  Note right of SG: Δ intents=[]
  Note right of SG: Δ chat_history+=User("面談したい")

  SG->>IR: NLU処理開始
  Note right of IR: Δ intents=[GOAL_TRIGGER]

  IR->>GST: intent=GOAL_TRIGGER
  Note right of GST: Δ dialogue_mode=SLOT_FILLING
  Note right of GST: Δ step_context={"current_job": {...}}
  Note right of GST: Δ goal_phase=NOT_STARTED
  Note right of GST: Δ slots_contexts={"current_job": {...}}

  GST->>SST: SLOT_FILLINGモードへ
  Note right of SST: Δ slot_context={"current_job": {...}}
  Note right of SST: Δ slot_context.phase="NOT_STARTED"
  Note right of SST: Δ slot_context.missing_items=["company_name", "position"]

  SST->>SE: スロット充填実行へ
  Note right of SE: Δ slot_context={"current_job": {...}}

  SE->>SP: ポリシー判定へ
  Note right of SP: 【missing_itemsあり】<br>Δ next_slot="company_name"）
  Note right of SP: 【missing_itemsなし】<br>Δ slot_context.phase="PROCESSED"<br>next_slot=None）

  SP->>GP: 次アクション決定済
  Note right of GP: Δ goal_phase=EXECUTION
  Note right of GP: （スロット収集待ち）

  GP->>RN: 応答生成へ
  Note right of RN: Δ response="現職についてヒアリングを開始してよろしいですか？"

  RN->>EG: 応答生成完了
  Note right of EG: Δ chat_history+=AI("現職についてヒアリングを開始してよろしいですか？")
  EG-->>U: 「それでは現職についてヒアリングを開始してよろしいですか？」


  %% === ターン3: ユーザーが「はい」で確認 ===

  Note over U, EG: ターン3: 確認「はい」
  U->>INV: 「はい」
  Note right of INV: Δ query="はい"

  INV->>SG: グラフ実行開始
  Note right of SG: Δ chat_history+=User("はい")

  SG->>IR: NLU処理開始
  Note right of IR: Δ intents=[ACKNOWLEDGE]

  IR->>GST: intent=ACKNOWLEDGE
  Note right of GST: Δ dialogue_mode=SLOT_FILLING
  Note right of GST: Δ goal_phase=EXECUTION
  Note right of GST: Δ slots_contexts={"current_job": SlotContext(phase="pending")}

  GST->>SST: スロット状態追跡へ
  Note right of SST: Δ slot_context=SlotContext(name="current_job")
  Note right of SST: Δ slot_context.phase="filling"
  Note right of SST: Δ slot_context.missing_items=["company_name", "position"]
  Note right of SST: Δ slot_context.filled_items=[]

  SST->>SE: スロット充填実行へ
  Note right of SE: （入力整形）

  SE->>SP: ポリシー判定へ
  Note right of SP: Δ slot_context.missing_items=["company_name", "position"]
  Note right of SP: （company_name未入力→質問）

  SP->>GP: 次アクション決定済
  GP->>RN: 応答生成へ
  Note right of RN: Δ response="現職の会社名を教えてください。"

  RN->>EG: 応答生成完了
  Note right of EG: Δ chat_history+=AI("現職の会社名を教えてください。")
  EG-->>U: 「現職の会社名を教えてください。」


  %% === ターン4: ユーザーが会社名を入力 ===

  Note over U, EG: ターン4: 会社名入力
  U->>INV: 「株式会社○○です。」
  Note right of INV: Δ query="株式会社○○です。"

  INV->>SG: グラフ実行開始
  Note right of SG: Δ chat_history+=User("株式会社○○です。")

  SG->>IR: NLU処理開始
  Note right of IR: Δ intents=[SLOT_INFORM]

  IR->>GST: intent=SLOT_INFORM
  Note right of GST: （dialogue_mode=SLOT_FILLING維持）

  GST->>SST: スロット状態追跡へ
  Note right of SST: Δ slot_context.items.company_name="株式会社○○"
  Note right of SST: Δ slot_context.filled_items=["company_name"]
  Note right of SST: Δ slot_context.missing_items=["position"]

  SST->>SE: スロット充填実行へ
  Note right of SE: （入力整形）

  SE->>SP: ポリシー判定へ
  Note right of SP: （position未入力→質問）

  SP->>GP: 次アクション決定済
  GP->>RN: 応答生成へ
  Note right of RN: Δ response="現在の職種を教えてください。"

  RN->>EG: 応答生成完了
  Note right of EG: Δ chat_history+=AI("現在の職種を教えてください。")
  EG-->>U: 「現在の職種を教えてください。」


  %% === ターン5: ユーザーが職種を入力 ===

  Note over U, EG: ターン5: 職種入力
  U->>INV: 「営業です。」
  Note right of INV: Δ query="営業です。"

  INV->>SG: グラフ実行開始
  Note right of SG: Δ chat_history+=User("営業です。")

  SG->>IR: NLU処理開始
  Note right of IR: Δ intents=[SLOT_INFORM]

  IR->>GST: intent=SLOT_INFORM
  Note right of GST: （dialogue_mode=SLOT_FILLING維持）

  GST->>SST: スロット状態追跡へ
  Note right of SST: Δ slot_context.items.position="営業"
  Note right of SST: Δ slot_context.filled_items=["company_name", "position"]
  Note right of SST: Δ slot_context.missing_items=[]
  Note right of SST: Δ slot_context.phase="completed"
  Note right of SST: Δ slots_contexts.current_job=slot_context

  SST->>SE: スロット充填実行へ
  Note right of SE: （全スロット充填完了を確認）

  SE->>SP: ポリシー判定へ
  Note right of SP: Δ slot_context.phase="completed"
  Note right of SP: （スロット充填完了）

  SP->>GP: スロット充填完了
  Note right of GP: Δ goal_phase=COMPLETED
  Note right of GP: Δ step_contexts.hearing.phase="completed"

  GP->>RN: 応答生成へ
  Note right of RN: Δ response="ヒアリングは以上です。"

  RN->>EG: 応答生成完了
  Note right of EG: Δ chat_history+=AI("ヒアリングは以上です。")
  EG-->>U: 「ヒアリングは以上です。」

```





---
## 書き方サンプル.※修正しないこと。


```mermaid
sequenceDiagram
  autonumber
  actor U as User
  participant N1 as intake_node
  participant N2 as clarify_node
  participant N3 as intake_node_2
  participant N4 as retrieve_kb_node
  participant N5 as compose_node

  U->>N1: 「住所変更したい」
  Note right of N1: Δ intent=PROCEDURE
  Note right of N1: Δ slots.procedure_type=address_change
  Note right of N1: Δ missing_slots=[contract_type]

  N1->>N2: (missing_slotsあり)
  Note right of N2: Δ clarifying_question="契約種別は？"
  Note right of N2: Δ next_action=wait_user
  N2-->>U: 「契約種別は？」

  U->>N3: 「個人です」
  Note right of N3: Δ slots.contract_type=personal
  Note right of N3: Δ missing_slots=[]
  Note right of N3: Δ next_action=search

  N3->>N4: (search)
  Note right of N4: Δ kb_hits=[KB_202]
  Note right of N4: Δ tool_trace+=kb_search

  N4->>N5: (compose)
  Note right of N5: Δ final_answer=...
  Note right of N5: Δ next_action=done
  N5-->>U: 「住所変更の手順は…」


```
