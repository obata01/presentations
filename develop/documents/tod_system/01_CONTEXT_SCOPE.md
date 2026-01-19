# 01_CONTEXT_AND_SCOPE - Dialogue System Design Pack
本章は **「外部との境界（Context）と、作る範囲（Scope）」** を固定するためのドキュメントです。  
以降の要求・設計・実装（State/Node/Workflow）がブレないよう、**責任分界**と**外部依存**を明確にします。

---

## 1. Purpose（この章の目的）
- **責任分界の明確化**：本システムが何を担い、何を担わないかを固定する
- **外部依存の洗い出し**：チャネル、認証、KB/DB、ツール、監査などの関係を可視化する
- **非機能の起点**：PII、監査、タイムアウト、SLA、コスト等の議論を開始できる状態にする
- **実装契約への接続**：後続の State/Node/Workflow をこの境界に従って設計する

---

## 2. System Overview（システムの要約）
### 2.1 System Name（仮）
- Dialogue System / Task-oriented Agent（LangGraph）

### 2.2 One-liner
- ユーザーの自然文入力から意図と必要情報を抽出し、**確認質問・検索・ツール実行**を経て解決へ導く。解決不能時は **安全に縮退**し、必要なら **人へ引き継ぐ**。

---

## 3. Business Context（ビジネス文脈）
### 3.1 Primary Actors（主な利用者）
- **End User（ユーザー）**：質問・手続き依頼を行う
- **Operator（オペレーター）**：人手対応・エスカレーション処理
- **Admin（管理者）**：設定・監査・運用管理

### 3.2 Representative Use Cases（代表ユースケース）
> 詳細な要件は 02 に記載。ここでは境界を決めるための“代表例”を置く。

- UC-01: FAQ回答（KB検索→根拠付き回答）
- UC-02: 手続き案内（不足情報の確認→手順提示）
- UC-03: チケット起票（解決不能→人手へ）

---

## 4. Scope（作る範囲）
### 4.1 In Scope（本システムが責任を持つ）
- チャネル入力の受領と応答（API/Adapter含む）
- 意図分類（Intent Recognition）とスロット抽出・不足判定
- 確認質問（Clarify）による情報補完
- KB検索・手順提示（必要ならRAG/検索）
- 条件付きの外部ツール実行（CRM参照、チケット起票等）
- 例外処理（retry / timeout / fallback / handoff）
- 監査ログ・トレース・基本メトリクス（最小構成）
- セッション状態管理（Checkpoint）

### 4.2 Out of Scope（本システムが責任を持たない）
- 公式判断が必要な業務の自動承認（返金可否など）
- 外部DB/CRMのデータ品質保証・修正
- チャネルプロダクト自体の提供（LINEやTeamsの運用基盤）
- 高度な推薦/最適化モデルの新規構築（別PJ）

### 4.3 Assumptions（前提）
- KB/CRM/Ticketなどの外部システムは既に存在し、APIまたはDBアクセス手段がある
- 認証・認可は既存IdP（OIDC等）を利用する
- 対話の永続化（保持期間・削除方針）は組織ポリシーに従う（詳細は 13/14/16）

---

## 5. System Boundary（システム境界：コンテキスト図）
> 外部との接点を可視化し、依存と責任分界を固定する。

```mermaid
flowchart LR
  %% Actors
  U[End User] -->|message| CH["Channel / UI<br/>Web・LINE・Teams等"]
  OP[Operator] -->|ops| OPS["Ops Console"]
  AD[Admin] -->|config| ADM["Admin Console"]

  %% System
  subgraph SYS["Dialogue System (This System)"]
    API["API / Backend"] --> ORCH["LangGraph Orchestrator"]
    ORCH --> LLM["LLM Client"]
    ORCH --> NODES["Nodes<br/>NLU / DM / NLG / Tool"]
    ORCH --> CP["Checkpoint Store"]
    ORCH --> AUD["Audit Log Sink"]
  end

  CH --> API
  OPS --> API
  ADM --> API

  %% External systems
  NODES --> KB["Knowledge Base / Search"]
  NODES --> CRM["CRM / Customer DB"]
  NODES --> TKT["Ticketing System"]
  NODES --> NOTIF["Notification<br/>Email/SMS/Push"]
  API --> IDP["Auth / IdP"]
````

---

## 6. External Interfaces（外部インターフェース一覧）

> 具体的なタイムアウト値・冪等性・エラー分類は 09/07 に詳細化する。ここでは境界の棚卸し。

| External     | Purpose  | Interface    | Data Sensitivity | Key Constraints | Default Failure Strategy |
| ------------ | -------- | ------------ | ---------------- | --------------- | ------------------------ |
| Channel/UI   | 入出力      | Webhook/REST | PII含む可能性         | 文字数・改行・添付       | エラー応答＋再送誘導               |
| Auth/IdP     | 認証/認可    | OIDC/SAML    | 個人情報             | token期限/権限      | 再認証誘導                    |
| KB/Search    | FAQ/手順検索 | REST/Search  | 公開〜機密            | 更新頻度/品質         | 「不確実」提示＋handoff          |
| CRM/DB       | 顧客情報参照   | REST/DB      | **PII高**         | 最小権限/監査         | 参照せず継続 or handoff        |
| Ticketing    | エスカレーション | REST         | 機密               | 冪等性/二重起票        | retry→fallback           |
| Notification | 通知       | REST         | 連絡先PII           | 再送制御            | キュー化/後送                  |

---

## 7. Conversation Lifecycle（外部境界に関わる状態遷移）

> 内部の詳細Stateは 04、DMフローは 05。ここでは「境界の観点」で粗く示す。

```mermaid
stateDiagram-v2
  [*] --> Idle

  Idle --> Receive: "user_message"
  Receive --> Process: "invoke graph"
  Process --> Respond: "answer"
  Respond --> Idle

  Process --> WaitUser: "clarify needed"
  WaitUser --> Receive: "user_reply"

  Process --> Handoff: "cannot resolve / policy"
  Handoff --> Idle

  Process --> Error: "exception / timeout"
  Error --> Idle
```

---

## 8. What data crosses the boundary（境界をまたぐデータ）

### 8.1 Inbound（外部→本システム）

* ユーザー入力テキスト（PII含む可能性）
* チャネルメタ情報（ユーザーID、タイムスタンプ、添付の有無等）
* 認証トークン（IdP）
* 外部API応答（KB記事、顧客情報、チケットID等）

### 8.2 Outbound（本システム→外部）

* ユーザーへの応答（文章、リンク、確認質問）
* ツール要求（KB検索クエリ、CRM参照キー、チケット起票ペイロード）
* 監査ログ・メトリクス

### 8.3 Data handling notes（方針の起点）

* PIIマスキング、保持期間、監査要件は 13/14/16 で確定する
* tool_resultの保存は “全文ではなく要約＋参照ID” を原則（詳細は 09/04）

---

## 9. Open Questions（未決事項）

* どのチャネルをMVP対象にするか（Webのみ/複数）
* CRM参照の最小属性（必要なフィールド）
* KBの検索方式（キーワード/ベクトル/ハイブリッド）
* Handoff条件の具体（どのリスクで人へ渡すか）
* 保持期間（Checkpoint / Audit / messages）と削除方法
