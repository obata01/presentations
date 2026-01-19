# 10 Data & KB - Dialogue System (KB / RAG)

本ドキュメントは、対話システムで **KB（Knowledge Base）/ RAG** を利用する場合のデータ設計と運用方針を定義する。  
ツール統合は `09_TOOLS_AND_INTEGRATIONS.md`、セキュリティは `13_SECURITY_AND_GUARDRAILS.md` を正とする。

---

## 1. Goals（目的）
- KB/RAG の「何を・どこから・どう更新して・どう参照するか」を明確にする
- 権限（ACL）とPIIの扱いを統一し、漏洩リスクを下げる
- 取得失敗時でも破綻しない代替戦略（fallback）を用意する

---

## 2. Scope（対象）
- ドキュメント型KB（PDF/社内Wiki/マニュアル/FAQ/規程）
- 構造化KB（業務DB、FAQテーブル、ナレッジ記事メタデータ）
- 検索（BM25/ベクトル/ハイブリッド）と、必要に応じた再ランキング
- ここでは “概念設計と運用方針” を扱い、実装詳細は別途（必要なら）扱う

---

## 3. Data Model（データ構造）

### 3.1 Document Object（ドキュメント共通）
各チャンク（またはドキュメント）に最低限つけるメタ情報：

- `doc_id`: 一意ID
- `source`: 由来（wiki, drive, confluence, db, faq, etc）
- `title`: タイトル
- `url_ref`: 参照先（URLまたは内部参照ID）
- `updated_at`: 最終更新
- `owner`: 管理者/管理チーム
- `acl`: アクセス制御（後述）
- `content`: 本文（チャンクの場合は chunk text）
- `chunk_id`: チャンクID（任意）
- `tags`: 任意タグ（手続き名、部門、対象者など）

> “全文” をStateに入れない。Stateには参照IDや、短い要約のみ。

### 3.2 FAQ Object（FAQ/QAの場合）
- `faq_id`
- `QUESTION`
- `answer`
- `category`
- `acl`
- `updated_at`

---

## 4. Indexing & Retrieval（インデックスと検索）

### 4.1 Index types（推奨）
- **Hybrid retrieval**（推奨）：キーワード + ベクトル（どちらか単独より安定）
- 再ランキング（必要なら）：上位N件を rerank して精度を上げる

### 4.2 Chunking policy（チャンク方針）
- 章・見出し単位を基本（意味境界を優先）
- チャンクは短すぎない（文脈欠落を防ぐ）
- チャンクには必ず `title/heading` をメタとして含める（回答で引用しやすくする）

### 4.3 Retrieval output（取得結果の扱い）
取得結果は次のいずれかで扱う：
- RNへ渡す：`retrieved_refs`（doc_id/chunk_idの一覧）＋ `snippets`（短い抜粋）
- tool_resultに保持：巨大にならない範囲で上位数件のみ

---

## 5. Sync / Update（更新・同期）

### 5.1 Update strategy
- 更新方式：定期同期（バッチ）＋重要ソースはイベント駆動（可能なら）
- 最低限必要：
  - 更新検知（updated_at差分）
  - 再チャンク/再埋め込み（必要な場合）
  - 古いインデックスのクリーンアップ

### 5.2 Versioning
- `updated_at` と `source_revision`（可能なら）を保持
- 回答時は「どの版を参照したか」をログに残す（監査に有効）

---

## 6. Access Control（参照範囲：権限/ACL）

### 6.1 ACL model（最小）
- `public` / `internal` / `restricted` の3段階（最小）
- 可能なら `allowed_groups`（部署/ロール）を持つ

### 6.2 Enforcement（強制）
- retrieval時点でフィルタ（許可されたものだけ検索/返却）
- 応答生成時にも “参照してよい情報のみ” を入力に渡す（多層防御）

---

## 7. PII / Masking（PIIとマスキング）

### 7.1 Storage
- PIIを含む文書は `acl=restricted` とし、対象ユーザ/権限を明確化
- ベクトル化・ログ出力の扱いはセキュリティ方針に従う

### 7.2 Logging
- 取得した `doc_id/chunk_id` のみログに残し、本文スニペットは最小限
- スニペットを残す場合はマスキング（住所/氏名/番号）

> 詳細方針は `13_SECURITY_AND_GUARDRAILS.md` を正とする。

---

## 8. Fallback Strategies（取得失敗時の代替戦略）

KB/RAGが失敗しても対話を破綻させない。

### 8.1 Retrieval fails（検索失敗）
- “見つからない” を明示し、ユーザに追加情報を依頼（SLOT_FILLINGへ寄せる）
- 代替：FAQ（構造化KB）を優先検索してみる

### 8.2 Low confidence（自信が低い）
- 回答を断定せず、確認質問へ
- 参照候補を提示し「どれの話か」を特定する

### 8.3 Permission denied（権限不足）
- 権限不足を明示し、参照可能範囲の案内
- 必要なら handoff（人手対応）へ

### 8.4 Partial outage（部分障害）
- “いま検索が不安定” を伝え、再試行または代替手順（問い合わせ先）へ

---

## 9. Where to integrate in workflow（ワークフロー上の組み込み位置）

推奨の組み込み先：
- `GE`（STEP_BY_STEP）：手順の根拠（規程/手順書）を引く
- `SE`（SLOT_FILLING）：候補検索（住所候補、商品候補、FAQ候補など）
- `NP`（Non-task）：一般質問の回答根拠として引く
- `RN`：最終応答に参照情報を反映（参照IDや出典名を必要に応じて提示）

---

## 10. Open Questions（未決事項）
- 取得件数（top_k）、ハイブリッド比率、rerank有無
- チャンク粒度（トークン長）と章構造の扱い
- 参照提示の方針（出典URLを出すか、社内向けのみか）
- restricted文書の埋め込み/ログの扱い（厳格運用）
