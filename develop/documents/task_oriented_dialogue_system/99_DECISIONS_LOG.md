# 99 Decisions Log - Dialogue System (Mini ADR)

本ドキュメントは、対話システム設計パックの **設計判断ログ（簡易ADR）** を記録する。  
「何を選んだか / なぜ / 代替案 / 影響範囲」を短く残し、後から意思決定の根拠を辿れる状態にする。

---

## How to write（書き方）

各エントリは以下のテンプレで記録する。

- **ID**: ADR-YYYYMMDD-XXX
- **Status**: Proposed / Accepted / Deprecated
- **Decision**: 何を選んだか（1〜2行）
- **Context**: なぜ必要だったか（背景）
- **Rationale**: なぜそれが良いか（理由）
- **Alternatives**: 代替案（箇条書きで短く）
- **Consequences**: 影響範囲（どのドキュメント/実装/テストに効くか）
- **Notes**: 補足（任意）

---

## ADR List（一覧）

> 初期状態ではテンプレを並べる。決定が発生したら追記する。

---

### ADR-20260116-001
- **Status**: Accepted
- **Decision**: Mermaid（VSCode `bierner.markdown-mermaid`）では、subgraphタイトル/ノードラベルを `["..."]` で囲う運用を標準とする。
- **Context**: 特定文字（括弧・記号等）でParse errorが発生し、図が安定しない。
- **Rationale**: `["..."]` で囲うとパースが安定し、設計図が壊れにくい。
- **Alternatives**:
  - 記号を避ける（括弧を使わない）
  - Mermaidレンダラを変更する
- **Consequences**:
  - 影響：全ドキュメントのMermaid図（03/05/07など）
  - テスト：図のビルド/プレビュー確認
- **Notes**: `<br/>` 改行も併用する。

---

### ADR-20260116-002
- **Status**: Accepted
- **Decision**: 応答経路を `RP → RN → EG` に統一し、task/non-taskはRPで合流させる。
- **Context**: 返答生成ロジックが分散するとテンプレ・安全対応・監視が分裂する。
- **Rationale**: NLG経路を統一すると、テンプレ管理、禁則対応、観測（RN失敗）を一箇所に集約できる。
- **Alternatives**:
  - taskとnon-taskで別NLGを持つ
  - NPが直接テキストを返す
- **Consequences**:
  - 影響：05（ワークフロー）、08（テンプレ）、14（観測）
  - テスト：統合テストで両経路がRP合流することを確認（15）
- **Notes**: RPが “NLG入口の単一窓口” となる。

---

### ADR-20260116-003
- **Status**: Accepted
- **Decision**: DM内部は `DST / DAE / DP` の3ブロックに分け、HierTOD風に `STEP_BY_STEP` と `SLOT_FILLING` を `dialogue_mode` で統合する。
- **Context**: 手順実行とスロット収集が混在するタスクを、1つのDMで一貫して扱いたい。
- **Rationale**: modeにより分岐しつつ、最終的にGPへ合流でき、拡張（slot/step追加）にも強い。
- **Alternatives**:
  - 2系統（slot専用DM / step専用DM）に分割
  - 常にslot充填してからstepへ（固定順序）
- **Consequences**:
  - 影響：05（ワークフロー）、04（State：dialogue_mode）、06（ノード仕様）
  - テスト：SLOT_FILLING/STEP_BY_STEP両方のE2E（15）
- **Notes**: GST後に `dialogue_mode` でSST/GEへ分岐。

---

### ADR-20260116-004
- **Status**: Proposed
- **Decision**: entity抽出はIRでは最小化し、主にDAE（SE/GE）で行う方針とする。
- **Context**: IRに多機能を持たせると誤判定の影響が大きく、責務が肥大化しやすい。
- **Rationale**: IRはルーティングに集中し、抽出/正規化は実行側で扱うと役割分担が明確。
- **Alternatives**:
  - IRでentitiesを確定し、後段はslot投入だけにする
  - IRとSEで二重抽出する
- **Consequences**:
  - 影響：04（entities/slotsの責務）、06（IR/SE仕様）、08（IR/SEプロンプト）
  - テスト：slot充填系ケースで抽出漏れがないか（15）
- **Notes**: 最終決定は実装・精度で判断。

---

### ADR-20260116-005
- **Status**: Proposed
- **Decision**: tool呼び出しは原則 DAE（GE/SE）に閉じ、ツール許可リストはノード単位で運用する。
- **Context**: PolicyやNLGにツール実行が混ざると権限管理と監査が難しくなる。
- **Rationale**: 実行責務をDAEに集中し、監査・リトライ・冪等性を統一しやすい。
- **Alternatives**:
  - 専用TOOLノードを用意し、全ツールはそこで実行
  - Policyがtool_callを決めてそのまま実行
- **Consequences**:
  - 影響：09（I/F）、13（ガードレール）、07（リトライ規約）
  - テスト：timeout/retry超過（15）
- **Notes**: 実装都合で専用TOOLノードを追加する可能性あり。

---

## Blank Template（追記用テンプレ）

### ADR-YYYYMMDD-XXX
- **Status**: Proposed
- **Decision**:
- **Context**:
- **Rationale**:
- **Alternatives**:
- **Consequences**:
- **Notes**:
