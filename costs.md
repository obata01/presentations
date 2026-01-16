Bedrockで「ファインチューニング（モデルカスタマイズ）したモデル」を**ホストして推論**する場合、料金はざっくり **(1)学習 (2)保管 (3)推論（ホスティング）** の3本立てです。モデルと推論モードで課金形態が変わります。([Amazon Web Services, Inc.][1])

---

## 料金の内訳（何にいくら掛かる？）

### 1) 学習（Fine-tuning）

* **Supervised fine-tuning（教師ありFT）**：学習で処理した**総トークン数（= 学習データ tokens × epoch数）**に応じて課金、という整理です。([Amazon Web Services, Inc.][1])
* **Reinforcement fine-tuning**：ワークフロー全体が**時間課金（hourly）**と明記されています。([Amazon Web Services, Inc.][1])

### 2) カスタムモデル保管（Storage）

* **「カスタムモデル1つあたり月額」**が掛かります（モデル表に “Price to store each custom model per month” が出ます）。([Amazon Web Services, Inc.][1])

### 3) 推論（= いわゆるホスティング費用）

ここが一番誤解されやすいです。Bedrockのカスタムモデル推論は主に2系統あります。

**A. Provisioned Throughput（時間課金：MU/時）**

* カスタムモデル利用に **Provisioned Throughputが必須**になるケースがあり、**購入したProvisioned Throughputは時間課金で、削除するまで課金が継続**します。([AWS ドキュメント][2])
* 価格は**モデル / MU数 / コミット期間（なし・1か月・6か月）**で決まります。([AWS ドキュメント][2])
* さらに重要：**カスタムモデルのMU単価は、元になったベースモデルと同じ**と明記されています。([AWS ドキュメント][2])

**B. On-demand（トークン課金：in/out tokens）**

* 一部のカスタムモデルは **オンデマンド（従量・トークン課金）**で推論できます（＝「常時起動の時間課金」を必ずしも払わなくてよい）。([AWS ドキュメント][3])
* ただし **対応リージョン/モデルに制約**があります。例：Bedrockの「カスタムモデルのオンデマンド推論デプロイ」は **US East (N. Virginia) / US West (Oregon)** で案内されています。([AWS ドキュメント][3])

---

## 具体例（公式ページに載っている数字の例）

※下は **Meta Llama 2（US East/West）**の価格例です（モデルによって違います）。([Amazon Web Services, Inc.][1])

### 例1：Fine-tuning（教師あり）＋保管

* 学習：**$0.00149 / 1,000 tokens**（Llama 2 Pretrained 13B）または **$0.00799 / 1,000 tokens**（70B）([Amazon Web Services, Inc.][1])
* 保管：**$1.95 / 月（custom model）**([Amazon Web Services, Inc.][1])

### 例2：カスタムモデルを「ホスト」（Provisioned Throughput）

* Provisioned Throughput：**$21.18 / 時 / MU（1か月コミット）**、**$13.08 / 時 / MU（6か月）**（Llama 2系の例）([Amazon Web Services, Inc.][1])
* 月額イメージ（1MUを24/7稼働）

  * 30日（720時間）だと：21.18×720
    = 21.18×700（14,826） + 21.18×20（423.6）
    = **$15,249.6 / 月**
  * 31日（744時間）だと：21.18×744 = **$15,757.92 / 月**（これは公式の計算例としても掲載）([Amazon Web Services, Inc.][1])

> ここが「BedrockでFTモデルを“ホスト”すると月いくら？」の中心で、**MUを何個買うか**でほぼ比例します。([AWS ドキュメント][2])

---

## 補足：別パターン（Custom Model Import の“ホスト”課金）

もし「Bedrockに重みを**インポート**してホストする」系（Custom Model Import）だと、**“モデルコピーが稼働していた時間”に対して5分単位で課金**＋**CMUの月額保管**という体系です。
例として、US East/West だと **$0.05718 / CMU / 分（5分窓課金）**、**$1.95 / CMU / 月**が掲載されています。([Amazon Web Services, Inc.][1])
（必要CMUはモデルサイズ等で決まり、例として Llama 3.1 8B 128Kは2CMU、70B 128Kは8CMUといった目安も載っています。）([Amazon Web Services, Inc.][1])

---

## どれを見積もればいい？

あなたの「ホスト料金」を出すには、まずこの分岐だけ決めればOKです：

1. **どのベースモデルをFTする？（Nova / Llama / Cohere…）**
2. 推論は **Provisioned Throughput（時間課金）**？ それとも **On-demand（トークン課金）**でいけるモデル/リージョン？([AWS ドキュメント][2])

もし「使いたいモデル名」「リージョン（例：東京）」と、だいたいの **入力/出力トークン** と **常時稼働が必要か（24/7か、昼だけか）**が分かれば、公式表の数字で **月額レンジ**まで落として計算して出します。

[1]: https://aws.amazon.com/bedrock/pricing/ "Amazon Bedrock Pricing – AWS"
[2]: https://docs.aws.amazon.com/bedrock/latest/userguide/prov-throughput.html "Increase model invocation capacity with Provisioned Throughput in Amazon Bedrock - Amazon Bedrock"
[3]: https://docs.aws.amazon.com/bedrock/latest/userguide/deploy-custom-model-on-demand.html "Deploy a custom model for on-demand inference - Amazon Bedrock"


できます。ただし先に大事な注意点です。

* **MU（Model Unit）1あたりの「入力TPM/出力TPM（tokens/min）」は、モデルごとに固定**…なのですが、**AWSはその具体値を公開していない**ケースが多く、価格ページにも「詳細はアカウント担当へ」と書かれています。([AWS ドキュメント][1])
* なのでここでは「MU=1で何req/min？」を**公式に断定できません**。代わりに、**(A) Provisioned Throughput（PT）が買えるモデル/リージョン**と、**(B) On-demand の公式クォータ（req/min・tokens/min）から“上限”として見積もる**、という形でまとめます。([AWS ドキュメント][2])

---

## 1) Provisioned Throughput（MU購入）できる代表バージョンとリージョン

| ファミリー             | 代表バージョン（例）                                                 | PT（MU）購入可否/リージョン                  | 備考                                                                     |
| ----------------- | ---------------------------------------------------------- | --------------------------------- | ---------------------------------------------------------------------- |
| Claude 3.5 Sonnet | `anthropic.claude-3-5-sonnet-20240620-v1:0:{18k/51k/200k}` | **us-west-2のみ** ([AWS ドキュメント][3]) | MU1あたりTPM/価格は公開されておらず「詳細は担当へ」扱い ([Amazon Web Services, Inc.][4])       |
| Llama 3.x         | 例：`meta.llama3-1-70b-instruct-v1:0:128k`                   | **us-west-2のみ** ([AWS ドキュメント][3]) | 同上（MU詳細は公開されないことが多い）([Amazon Web Services, Inc.][4])                   |
| Amazon Nova       | 例：`amazon.nova-pro-v1:0:{24k/300k}`                        | **us-east-1のみ** ([AWS ドキュメント][3]) | Nova系は“カスタムNovaもオンデマンド推論はベースと同額”の案内あり ([Amazon Web Services, Inc.][4]) |

> つまり **「東京リージョンでMU購入して運用」**という前提は、少なくともこの3つではそのまま当てはまらず、**PTを買えるリージョンが限られる**のが現状です。([AWS ドキュメント][3])

---

## 2) “MU1で何リクエスト捌ける？”の代替：On-demand公式クォータで上限見積り

MU1のTPMが非公開なので、ここでは **On-demand の公式クォータ（req/min と tokens/min）**を使って、「このくらいが上限になりやすい」という形にします。([AWS ドキュメント][2])

### On-demandクォータ（代表）

* **Claude 3.5 Sonnet**：req/min は多くのリージョンで **20**、tokens/min は **200,000**（“その他リージョン”扱い）([AWS ドキュメント][2])
* **Llama 3.1 70B Instruct**：req/min **400**、tokens/min **300,000** ([AWS ドキュメント][2])
* **Nova Pro**：req/min **250**、tokens/min **1,000,000** ([AWS ドキュメント][2])

### 2つの“ありがちな”リクエストサイズで、req/min上限を試算

* **軽め**：入力 500 / 出力 200（合計 700 tokens）
* **RAG寄り**：入力 2000 / 出力 400（合計 2400 tokens）

> req/min 上限 ≒ min( req/minクォータ, tokens/minクォータ ÷ 平均総tokens )

| モデル                    |           req/minクォータ |              tokens/minクォータ |       上限req/min（500+200） |     上限req/min（2000+400） |
| ---------------------- | --------------------: | --------------------------: | -----------------------: | ----------------------: |
| Claude 3.5 Sonnet      |  20 ([AWS ドキュメント][2]) |   200,000 ([AWS ドキュメント][2]) |    min(20, 285) = **20** |    min(20, 83) = **20** |
| Llama 3.1 70B Instruct | 400 ([AWS ドキュメント][2]) |   300,000 ([AWS ドキュメント][2]) |  min(400, 428) = **400** | min(400, 125) = **125** |
| Nova Pro               | 250 ([AWS ドキュメント][2]) | 1,000,000 ([AWS ドキュメント][2]) | min(250, 1428) = **250** | min(250, 416) = **250** |

---

## 3) コスト（参考）：On-demandの“1リクエストあたり”概算

MU（PT）の $/h が出せないので、代わりに **On-demand（$ / 1k tokens）**で “1リクエストいくら” を同じ2パターンで概算します。

### 単価（代表）

* **Claude 3.5 Sonnet**：入力 $0.006 / 出力 $0.03（※掲載リージョンは限定。価格表の記載に従う）([Amazon Web Services, Inc.][4])
* **Meta Llama 3.3 Instruct 70B**：入力/出力とも $0.00072（AWSブログ例）([Amazon Web Services, Inc.][5])
* **Amazon Nova Pro**：入力 $0.0008 / 出力 $0.0032（AWSブログ例）([Amazon Web Services, Inc.][5])

### 1リクエスト概算（入力Tin, 出力Tout）

> cost ≒ (Tin/1000)*Pin + (Tout/1000)*Pout

| モデル               | 500in/200out | 2000in/400out |
| ----------------- | -----------: | ------------: |
| Claude 3.5 Sonnet |      $0.0090 |       $0.0240 |
| Llama 3.3 70B     |    $0.000504 |     $0.001728 |
| Nova Pro          |     $0.00104 |      $0.00288 |

---

## ここから先（MU1の“本当の”req/minと$/hを出す方法）

MU購入（Provisioned Throughput by Model Units）で「**MU1あたり何TPMか**」「**MU1が$/hいくらか**」は、モデル/リージョン/契約（1か月・6か月等）で変わり、**公開されないことがある**ため、最終的には **BedrockのPT購入画面（またはAWS担当）**で確認するのが確実です。([Amazon Web Services, Inc.][4])

---

もしよければ、次を1行で教えてください（こちらから質問してすみません。最短で実務の数字に落とすためです）：

* 使うリージョンは **東京で呼びたい**？それとも **PT購入できるus-west-2/us-east-1に寄せる**？
* 平均の **入力/出力トークン**（だいたいでOK）

これが分かれば、**「オンデマンド vs PT（MU購入）」の損益分岐（何req/min・何時間稼働でPTが得か）**を、あなたの前提で“ざっくり一枚”にまとめます。

[1]: https://docs.aws.amazon.com/bedrock/latest/userguide/prov-throughput.html "Increase model invocation capacity with Provisioned Throughput in Amazon Bedrock - Amazon Bedrock"
[2]: https://docs.aws.amazon.com/general/latest/gr/bedrock.html "Amazon Bedrock endpoints and quotas - AWS General Reference"
[3]: https://docs.aws.amazon.com/bedrock/latest/userguide/prov-thru-supported.html "Supported Region and models for Provisioned Throughput - Amazon Bedrock"
[4]: https://aws.amazon.com/bedrock/pricing/ "Amazon Bedrock Pricing – AWS"
[5]: https://aws.amazon.com/blogs/machine-learning/demystifying-amazon-bedrock-pricing-for-a-chatbot-assistant/?utm_source=chatgpt.com "Demystifying Amazon Bedrock Pricing for a Chatbot Assistant"
