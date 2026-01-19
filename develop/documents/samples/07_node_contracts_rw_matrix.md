# Node Contracts ＋ R/W Matrix
対象：Dialogue System（LangGraph）

---

## 1. ノード契約テンプレ
- purpose: ノードの目的
- reads: 参照するStateキー
- writes: 更新するStateキー
- side_effects: 外部I/O
- failure: 失敗時の方針（リトライ/縮退/エスカレーション）
- output_format: LLM出力形式（必要なら）

---

## 2. 例：retrieve_kb_node
- purpose: KB検索を行いヒットを格納する
- reads: normalized_text, intent, slots
- writes: kb_hits, tool_trace+
- side_effects: KB API call
- failure:
  - timeout: retry 2 → fallback_node
  - empty_hits: compose_nodeへ（「見つからない」を明示）

---

## 3. 例：compose_node
- purpose: 根拠付き回答を生成する
- reads: intent, slots, kb_hits, policy_flags, messages
- writes: final_answer, messages+
- side_effects: none（LLMのみ）
- failure:
  - llm_error: retry 1 → fallback_node

---

## 4. R/Wマトリクス（全体俯瞰）
| state_key | intake | policy | clarify | retrieve_kb | retrieve_crm | compose | ticket | fallback |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| normalized_text | W | R | R | R | R | R | R | R |
| intent | W | R | R | R | R | R | R | R |
| slots | W | R | W | R | R/W | R | R | R |
| missing_slots | W | R | W | R | R | R | R | R |
| policy_flags | - | W | R | R | R | R | R | R |
| kb_hits | - | - | - | W | - | R | - | - |
| tool_trace | - | - | - | W | W | R | W | - |
| clarifying_question | - | - | W | - | - | - | - | - |
| final_answer | - | - | - | - | - | W | - | W |


