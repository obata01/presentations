
# コーディング規約

## 1. 基本原則
- **Type Safety**: 全ての関数に型ヒントを付ける。
- **Async First**: I/Oが発生する処理（APIコール、DB操作）は必ず `async/await` で記述する。
- **Docstring**: 全てのクラスとパブリックメソッドに Google Style の Docstring を記述する。

```python

def sample_function(arg1: int, arg2: str) -> bool:
    """説明は簡潔にしてドットで終えること.

    Args:
        arg1: 引数1
        arg2: 引数2

    Returns:
        戻り値
    
    Note:
        - 必要に応じてNoteに補足を記載.
        - Docstringは日本語で記載する.
        - Docstring側へのデータ型の記載は不要.
        - コード側に不要なコメントアウトを入れない.
        - 必要に応じてExceptionsも追記する.
    """
    return True
```

## 2. エラーハンドリング
- 例外は `src/common/exceptions.py` で定義されたカスタム例外クラスを使用する。
- ユーザーへの応答失敗時は、NLG層でフォールバックメッセージを生成すること。

