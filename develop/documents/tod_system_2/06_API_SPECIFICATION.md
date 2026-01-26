# 06_API_SPECIFICATION - API仕様書

※今後はSwagger UIを使用してAPI仕様を定義する予定。

---

## 1. API概要

### 1.1 基本情報

| 項目 | 内容 |
|------|------|
| **Protocol** | HTTP/1.1 |
| **Base URL** | `https://xxxxxxxxxx.com/v1` |
| **Content-Type** | `application/json` |
| **Character Encoding** | UTF-8 |

### 1.2 バージョニング

- URLパスに `/v1` を含める形式
- 破壊的変更時は `/v2` など新バージョンを作成

---

## 2. エンドポイント一覧

| Method | Endpoint | 説明 |
|--------|----------|------|
| GET | `/health` | ヘルスチェック |
| POST | `/chat/init` | セッション初期化 |
| POST | `/chat/message` | メッセージ送受信 |

---

## 3. エンドポイント詳細

### 3.1 ヘルスチェック

`GET /health`

サーバーの稼働状態を確認。

**レスポンス** (200 OK)
```json
{
  "status": "ok",
}
```

---

### 3.2 セッション初期化

`POST /chat/init`

チャットセッションを新規作成して初期メッセージを返す。

**リクエストスキーマ**
```python
class InitRequest(BaseModel):
    session_id: str
    user_id: str | None = None
```

**サンプル**
```json
{
  "session_id": "user_id + uuid など",
  "user_id": "user_12345"
}
```

**レスポンス** (200 OK)
```json
{
  "session_id": "user_id + uuid など",
  "message": "こんにちは！何かお手伝いできることはありますか？",
}
```

---

### 3.3 メッセージ送受信

`POST /chat/message`

対話のやり取りを行う。

**リクエストスキーマ**
```python
from typing import Annotated, Literal
from pydantic import BaseModel, Field
from enum import Enum

class Options(BaseModel):
    pass

class Command(str ,Enum):
    BACK = "back"

class TextQuery(BaseModel):
    kind: Literal["text"] = "text"
    text: str

class CommandQuery(BaseModel):
    kind: Literal["command"] = "command"
    command: Command

Query = Annotated[TextQuery | CommandQuery, Field(discriminator="kind")]

class MessageRequest(BaseModel):
    session_id: str
    user_id: str | None = None
    query: Query
    # options: Options | None = None
```

**サンプル1（テキスト送信）**
```json
{
"session_id": "user_id + uuid など",
  "user_id": "user_12345",
  "query": {
    "kind": "text",
    "text": "こんにちは"
  }
}
```

**サンプル2（コマンド送信）**
```json
{
  "session_id": "user_id + uuid など",
  "user_id": "user_12345",
  "query": {
    "kind": "command",
    "command": "back"
  }
}
```

**レスポンス** (200 OK)
```json
{
  "session_id": "thread_xyz789",
  "response": "こんにちは。何かご用ですか？",
}
```
