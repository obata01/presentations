# 技術スタック定義書

## 1. 開発言語・ランタイム
- **Language**: Python 3.11
- **Package Manager**: poetry

## 2. 主要フレームワーク・ライブラリ
- **Web Framework**: FastAPI (非同期I/Oを優先)
- **LLM Orchestration**: LangChain / LangGraph (対話フロー管理用)
- **Validation**: Pydantic v2 (全てのデータモデルに適用)
- **Natural Language Processing**: 
  - OpenAI API (GPT-4o)
  - SudachiPy (日本語形態素解析が必要な場合)

## 3. インフラ・データベース
- **Cache/State**: Redis (対話ステートの永続化)
- **Vector DB**: ChromaDB (知識ベースを導入する場合)

## 4. テスト・静的解析
- **Test**: pytest
- **Linter/Formatter**: Ruff, pylint
- **Type Check**: mypy
