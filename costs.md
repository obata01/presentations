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
