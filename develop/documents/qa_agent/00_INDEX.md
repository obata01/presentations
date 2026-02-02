# QAエージェントシステム

## 1. プロダクトの目的
入力されたユーザクエリに回答するためのデータを検索し回答するための自律駆動型エージェントシステム.

※Search MCP: Azure AI SearchやベクトルDBなどと接続して必要データを検索するシステム.


## 2. ディレクトリ構造
AIがファイルを配置する場所を以下の構造とする。

```text
/
├── docs/                 # 設計詳細・プロンプト定義
├── src/
│   ├── application/      # アプリケーション層
│   │   ├── nodes/        # ノード定義
│   │   ├── states.py     # 状態管理
│   │   └── workflows.py  # ワークフロー定義
│   ├── components/       # インフラ層
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
└── tests/                # 各モジュールのテスト
```
