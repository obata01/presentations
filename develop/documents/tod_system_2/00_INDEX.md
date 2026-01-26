# AI対話システム (Project Name: Aurora-Dialogue)

## 1. プロジェクトの目的
ユーザーからの自然言語入力を理解し、適切な文脈（コンテキスト）を維持しながら、人間らしく自然な応答を生成する汎用的な対話エージェントを構築します。

## 2. ディレクトリ構造
AIがファイルを配置する場所を以下の構造に固定します。

```text
/
├── docs/                 # 設計詳細・プロンプト定義
├── src/
│   ├── application/      # アプリケーション層
│   │   ├── nodes/        # ノード定義
│   │   ├── states.py     # 状態管理
│   │   └── workflows.py  # ワークフロー定義
│   ├── domain/           # ドメイン層
│   ├── infrastructure/   # インフラ層
│   │   ├── adapters/     # アダプター
│   │   ├── repositories/ # リポジトリ
│   │   └── tools/        # Tool定義
│   ├── common/           # 共通層
│   │   ├── lib/          # ライブラリ
│   │   ├── defs/         # model/enum/type定義
│   │   ├── schemas/      # シェーマ定義
│   │   ├── exceptions/   # エラー定義
│   │   └── config/       # 設定
│   ├── main.py           # エントリポイント
│   └── gunicorn.conf.py  # gunicorn設定
├── tests/                # 各モジュールのテスト
└── .cursorrules          # AIへの制約指示（AI駆動開発用）
```
