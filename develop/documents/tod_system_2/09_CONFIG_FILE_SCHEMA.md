# 09 CONFIG FILE SCHEMA - 設定ファイル仕様

## 1. 概要

設定ファイル（Config File）は、対話システムの実行時設定を定義するYAML形式のファイルです。LLMクライアント、ノード、アクション、チェックポイントの設定を一元管理します。

---

## 2. ルートスキーマ

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `llms` | LLMsConfig | ✓ | LLMクライアント設定 |
| `nodes` | NodeConfig[] | ✓ | ノード設定リスト |
| `actions` | ActionConfig[] | | アクション設定リスト |
| `checkpoint` | CheckpointConfig | | チェックポイント設定 |

---

## 3. LLMsConfig スキーマ

### 3.1 ルート構造

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `chat_clients` | ChatClients | ✓ | プロバイダー別クライアント定義 |

### 3.2 ChatClients

プロバイダーをキーとしたクライアント定義のマップ。

| プロバイダー | 型 | 説明 |
|-------------|-----|------|
| `bedrock` | BedrockClient[] | AWS Bedrock クライアント |
| `azure` | AzureClient[] | Azure OpenAI クライアント |

### 3.3 BedrockClient スキーマ

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `name` | string | ✓ | クライアント名（参照用） |
| `config.model_id` | string | ✓ | Bedrock モデルID |
| `config.region_name` | string | ✓ | AWSリージョン |
| `default_params.max_tokens` | int | | デフォルト最大トークン数 |

### 3.4 AzureClient スキーマ

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `name` | string | ✓ | クライアント名（参照用） |
| `config.model` | string | ✓ | モデル名 |
| `config.azure_deployment` | string | ✓ | デプロイメント名 |
| `config.azure_endpoint_env` | string | ✓ | エンドポイント環境変数名 |
| `config.api_key_env` | string | ✓ | APIキー環境変数名 |
| `config.openai_api_version` | string | ✓ | API バージョン |
| `default_params.temperature` | float | | デフォルト温度 |
| `default_params.max_completion_tokens` | int | | 最大生成トークン数 |
| `default_params.top_p` | float\|null | | Top-P サンプリング |

---

## 4. NodeConfig スキーマ

ノードごとのLLM設定を定義します。

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `name` | string | ✓ | ノード名（一意） |
| `chat_client` | ClientRef | | 使用するLLMクライアント参照 |
| `chat_params` | ChatParams | | ノード固有のパラメータ |
| `chat_prompt` | PromptConfig | ✓ | プロンプト設定 |

### 4.1 ClientRef スキーマ

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `provider` | string | ✓ | プロバイダー名（`azure`, `bedrock`） |
| `client_name` | string | ✓ | `llms.chat_clients` で定義したクライアント名 |

### 4.2 ChatParams スキーマ

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `temperature` | float\|null | 生成温度（0.0〜2.0） |
| `max_tokens` | int | 最大トークン数 |
| `top_p` | float\|null | Top-P サンプリング |

### 4.3 PromptConfig スキーマ

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `template_file` | string | ✓ | プロンプトテンプレートファイルパス |

---

## 5. ActionConfig スキーマ

アクション（外部処理）のLLM設定を定義します。構造は `NodeConfig` と同一です。

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `name` | string | ✓ | アクション名（一意） |
| `chat_client` | ClientRef | | 使用するLLMクライアント参照 |
| `chat_params` | ChatParams | | パラメータ設定 |
| `chat_prompt` | PromptConfig | ✓ | プロンプト設定 |

---

## 6. CheckpointConfig スキーマ

対話状態の永続化設定を定義します。

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `kind` | string | ✓ | ストレージ種別（`sqlite`, `postgres` 等） |
| `dsn` | string | ✓ | データソース名（接続先パス/URI） |

---

## 7. サンプル

```yaml
llms:
  chat_clients:
    bedrock:
      - name: sonnet
        config:
          model_id: "jp.anthropic.claude-sonnet-4-5-20250929-v1:0"
          region_name: ap-northeast-1
        default_params:
          max_tokens: 1024

      - name: haiku
        config:
          model_id: "jp.anthropic.claude-haiku-4-5-20251001-v1:0"
          region_name: ap-northeast-1
        default_params:
          max_tokens: 1024

    azure:
      - name: gpt-4o
        config:
          model: gpt-4o
          azure_deployment: gpt-4o
          azure_endpoint_env: AZURE_OPENAI_ENDPOINT
          api_key_env: AZURE_OPENAI_API_KEY
          openai_api_version: 2024-08-01-preview
        default_params:
          temperature: 0.5
          max_completion_tokens: 1024
          top_p: null

      - name: gpt-4.1
        config:
          model: gpt-4.1
          azure_deployment: gpt-4.1
          azure_endpoint_env: AZURE_OPENAI_ENDPOINT
          api_key_env: AZURE_OPENAI_API_KEY
          openai_api_version: 2024-08-01-preview
        default_params:
          temperature: 0.5
          max_completion_tokens: 1024
          top_p: null

      - name: gpt-4.1-mini
        config:
          model: gpt-4.1-mini
          azure_deployment: gpt-35-turbo-16k
          azure_endpoint_env: AZURE_OPENAI_ENDPOINT
          api_key_env: AZURE_OPENAI_API_KEY
          openai_api_version: 2024-08-01-preview
        default_params:
          temperature: 0.5
          max_completion_tokens: 1024
          top_p: null

nodes:
  - name: intent_recognition
    chat_client:
      provider: azure
      client_name: gpt-4.1-mini
    chat_params:
      temperature: 0.1
      max_tokens: 512
      top_p: 0.1
    chat_prompt:
      template_file: "nodes/natural_language_understanding/intent_recognition.lc.tpl"

  - name: slot_filling_machine
    chat_client:
      provider: azure
      client_name: gpt-4.1-mini
    chat_params:
      temperature: 0.1
      max_tokens: 512
      top_p: 0.1
    chat_prompt:
      template_file: "nodes/dialogue_management/slot_filling_machine.lc.tpl"

  - name: question_answer
    chat_client:
      provider: azure
      client_name: gpt-4.1-mini
    chat_params:
      temperature: 1.0
      max_tokens: 1024
      top_p: 0.4
    chat_prompt:
      # ※この下（template_file行）が画像に写っていません

  - name: job_recommend
    chat_prompt:
      template_file: nodes/response_generation/slots_confirm_all.lc.tpl

  - name: hearing_summary
    chat_client:
      provider: azure
      client_name: gpt-4.1-mini
    chat_params:
      temperature: 1.0
      max_tokens: 512
      top_p: 0.5
    chat_prompt:
      template_file: "nodes/response_generation/hearing_summary.lc.tpl"

actions:
  - name: profile_summary
    chat_client:
      provider: bedrock
      client_name: sonnet
    chat_params:
      temperature: null
      max_tokens: 512
      top_p: 0.5
    chat_prompt:
      template_file: "actions/profile_summary.lc.tpl"

  - name: job_recommend
    chat_client:
      provider: bedrock
      client_name: sonnet
    chat_params:
      temperature: null
      max_tokens: 512
      top_p: 0.5
    chat_prompt:
      template_file: "actions/job_recommend.lc.tpl"

checkpoint:
  kind: sqlite
  dsn: "/app/db/sqlite/checkpoints.sqlite"
```
