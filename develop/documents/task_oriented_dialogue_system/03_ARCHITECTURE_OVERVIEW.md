# 03 Architecture Overview - Dialogue System

本ドキュメントは、LangGraphベース対話システムのアーキテクチャを俯瞰する。  
実装詳細（Stateキー、ノード差分、例外規約）は `04_STATE_MODEL.md` / `06_NODE_SPECS.md` / `07_ERROR_HANDLING_AND_MODES.md` を正とする。

---

## 1. Architectural Goals（この図で伝えたいこと）
- 主要コンポーネント（NLU / DM(DST/DAE/DP) / NLG）の責務境界
- 依存方向（上位から下位へ、実装が依存すべき契約）
- 代表フロー（task / non-task）と合流点（RP→RN→EG）
- 拡張点（intent追加、slot追加、手順追加、外部ツール追加）

---

## 2. High-level Overview（概観図）

> 注意：Mermaidは `bierner.markdown-mermaid` 前提。subgraphやラベルは `["..."]` で囲う。

```mermaid
flowchart LR
  %% Actors
  U["User"]

  %% Interface / Entry
  subgraph UI["UI / Channel"]
    direction LR
    SG["Start Gate"]
    EG["End Gate"]
  end

  %% Core Runtime
  subgraph APP["Application Runtime (LangGraph)"]
    direction LR

    subgraph NLU["NLU"]
      direction LR
      IR["IR<br/>(Intent Recognition)"]
    end

    subgraph DM["DM - Dialogue Manager"]
      direction LR

      subgraph DST["DST - State Tracking"]
        direction TB
        GST["GST<br/>(Goal State Tracking)"]
        SST["SST<br/>(Slot State Tracking)"]
      end

      subgraph DAE["DAE - Dialogue Act Executor"]
        direction TB
        SE["SE<br/>(Slot-filling Executor)"]
        GE["GE<br/>(Goal Executor)"]
      end

      subgraph DP["DP - Policy"]
        direction TB
        SFP["SFP<br/>(Slot-filling Policy)"]
        GP["GP<br/>(Goal Policy)"]
      end
    end

    subgraph NLG["NLG"]
      direction LR
      RP["Response Proxy"]
      RN["Response Nodes"]
      NP["NP<br/>(Non-task Policy)"]
    end
  end

  %% State & External (conceptual)
  subgraph STATE["State / Storage (conceptual)"]
    direction TB
    S["LangGraph State<br/>(messages, intent_type, dialogue_mode, slots, goal_state, ...)"]
  end

  %% Main flow (simplified)
  U --> SG --> IR
  IR -->|"intent_type in [OOS, QUESTION, SMALL_TALK]"| NP --> RP --> RN --> EG
  IR -->|"intent_type not in [OOS, QUESTION, SMALL_TALK]"| GST
  GST -->|"dialogue_mode==SLOT_FILLING"| SST --> SE --> SFP --> GP --> RP
  GST -->|"dialogue_mode==STEP_BY_STEP"| GE --> GP
  EG --> U

  %% State read/write (conceptual)
  IR -.-> S
  GST -.-> S
  SST -.-> S
  SE -.-> S
  GE -.-> S
  SFP -.-> S
  GP -.-> S
  NP -.-> S
  RN -.-> S
