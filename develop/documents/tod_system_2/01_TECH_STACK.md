# 技術スタック定義書

## 1. 開発言語・ランタイム
- **Language**: Python 3.13
- **Package Manager**: uv

## 2. 主要フレームワーク・ライブラリ

### Web Framework: FastAPI
- **選択理由**
  - 非同期I/O対応で高スループット
  - Pydanticとの統合で型安全性が高い
  - 自動OpenAPIドキュメント生成
  - モダンなPython機能（型ヒント）を活用

### LLM Orchestration: LangChain / LangGraph
- **選択理由**
  - 対話フロー管理のデファクトスタンダード
  - 状態管理（State）機能が強力
  - LLMプロバイダーの切り替えが容易
  - コミュニティとエコシステムが充実

※その他の使用する技術については、pyproject.tomlを参照.

## 3. インフラ・データベース
- **DB**: SQLite(ローカル開発)/PostgreSQL(本番)

## 4. テスト・静的解析
- **Test**: pytest
- **Linter/Formatter**: Ruff, pylint
- **Type Check**: mypy
