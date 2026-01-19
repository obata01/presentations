# Runtime View（代表シナリオ＋State変化）
対象：Dialogue System（LangGraph）

---

## UC-01: FAQ回答（情報十分 → KB検索 → 回答）
```mermaid
sequenceDiagram
  autonumber
  actor U as User
  participant G as LangGraph
  participant L as LLM
  participant KB as KB

  U->>G: 質問
  G->>L: intake_node
  L-->>G: intent=FAQ, slots, normalized_text
  G->>L: policy_node
  L-->>G: policy=OK
  G->>KB: retrieve_kb_node(query)
  KB-->>G: kb_hits
  G->>L: compose_node(kb_hits)
  L-->>G: final_answer
  G-->>U: 回答
```

## State差分（例）
| Step | Node             | Writes（更新）                                |
| ---: | ---------------- | ----------------------------------------- |
|    1 | intake_node      | normalized_text, intent, slots, messages+ |
|    2 | policy_node      | policy_flags, messages+                   |
|    3 | retrieve_kb_node | kb_hits, tool_trace+                      |
|    4 | compose_node     | final_answer, messages+                   |

## UC-02: 手続き案内（不足確認 → 手順提示）

```mermaid
sequenceDiagram
  autonumber
  actor U as User
  participant G as LangGraph
  participant L as LLM
  participant KB as KB

  U->>G: 「住所変更したい」
  G->>L: intake_node
  L-->>G: intent=PROCEDURE, slots_partial, missing_slots

  G->>L: clarify_node
  L-->>G: clarifying_question
  G-->>U: 確認質問

  U->>G: 追加情報
  G->>L: intake_node
  L-->>G: slots_filled, missing_slots=[]
  G->>KB: retrieve_kb_node
  KB-->>G: procedure_docs
  G->>L: compose_node
  L-->>G: final_answer
  G-->>U: 手順回答
```

## UC-03: 解決不能 → チケット起票
```mermaid
flowchart TD
  start([START]) --> intake[Intake]
  intake --> policy[Policy]
  policy --> decide{解決可能？}
  decide -->|Yes| retrieve[Retrieve]
  retrieve --> compose[Compose]
  compose --> finish([END])

  decide -->|No| ticket[Ticketing]
  ticket --> finish

```


## 会話状態遷移（Lifecycle）

```mermaid
stateDiagram-v2
  [*] --> Idle
  Idle --> Intake: user_message
  Intake --> Clarify: missing_info
  Clarify --> WaitingUser: ask_question
  WaitingUser --> Intake: user_reply
  Intake --> Retrieve: sufficient_info
  Retrieve --> Compose
  Compose --> Deliver
  Deliver --> Idle
  Intake --> Escalate: cannot_resolve/policy_risk
  Escalate --> Idle
  Intake --> Error: exception
  Error --> Idle
```


