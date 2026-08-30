# pubmed_handler

PubMed論文データをElasticsearchに投入し、BM25全文検索を行うためのリポジトリです。

Elasticsearch は Apptainer (HPC/Slurm 環境) または Docker で起動できます。

---

## リポジトリ構成

```
pubmed_handler/
├── env/                          # Apptainer + Slurm 環境 (現行)
│   ├── build_es.sh               # elasticsearch.sif のビルド
│   ├── run_es.sh                 # Elasticsearch 起動
│   └── README.md                 # Apptainer 環境の詳細手順
│
├── previous_env/                 # Docker 環境 (旧)
│   ├── docker-compose.yml
│   ├── .env
│   └── README.md
│
├── prepare_with_parquet/         # インデックス作成スクリプト (現行)
│   ├── prepare_elasticsearch_parquet_article.py   # articles のみ (推奨)
│   └── prepare_elasticsearch_parquet.py           # articles + sentences + labels
│
├── archive_prepare/              # インデックス作成スクリプト (旧 / SQLite ベース)
│   ├── prepare_elasticsearch.py          # exact match アナライザー
│   ├── prepare_elasticsearch_stem.py     # porter_stem アナライザー
│   ├── prepare_elasticsearch_v2.py       # stem の安定版
│   ├── prepare_elasticnet.ipynb          # notebook 版 (article + sentence)
│   └── prepare_elasticsearch_pmc.ipynb   # PMC データ調査用
│
└── search_demo/                  # 検索デモ notebook
    ├── search_drugbank.ipynb
    ├── search_meddra.ipynb
    ├── search_pubchem.ipynb
    ├── search_rxnorm.ipynb
    ├── search_cell_ontology.ipynb
    └── overlap_sentence.ipynb
```

---

## データ

インデックス作成には `text_data_handler` リポジトリで生成した PubMed parquet を使用します。

| ファイル | 行数 | 内容 |
|---|---|---|
| `combined_articles.parquet` | 約3,820万 | 1記事1行（pmid, title, abstract, journal, year, mesh, ...） |
| `combined_sentences.parquet` | 約8,690万 | 1文1行（pmid, sent_id, sentence） |
| `combined_labels.parquet` | 約4,890万 | 1セクション1行（pmid, label_id, label, text） |

`DATA_DIR` 環境変数でデータディレクトリを指定します（デフォルト: カレントディレクトリ）。

---

## Elasticsearch 環境構築

### Apptainer (HPC/Slurm) — 推奨

詳細は [env/README.md](env/README.md) を参照してください。

```bash
# 1. SIF ビルド (初回のみ)
cd env
./build_es.sh

# 2. Elasticsearch 起動
./run_es.sh
```

起動後、`http://localhost:9200` で待ち受けます。

### Docker (ローカル開発)

```bash
cd previous_env
docker compose up -d
```

---

## インデックス作成

### 必要パッケージ

```bash
pip install elasticsearch pyarrow python-dotenv tqdm
```

### `.env` の設定

```bash
ES_HOST=http://localhost:9200
ES_USER=elastic
ES_PASSWORD=         # セキュリティ無効の場合は空
DATA_DIR=/path/to/data
```

### articles のみ投入（推奨）

```bash
python prepare_with_parquet/prepare_elasticsearch_parquet_article.py
```

作成されるインデックス:

| インデックス名 | 粒度 | 主なフィールド |
|---|---|---|
| `pubmed_articles` | 1記事1doc | pmid, title, abstract, journal, year, mesh, publication_types |

### articles + sentences + labels を一括投入

```bash
python prepare_with_parquet/prepare_elasticsearch_parquet.py
```

追加で作成されるインデックス:

| インデックス名 | 粒度 | 主なフィールド |
|---|---|---|
| `pubmed_sentences` | 1文1doc | pmid, sent_id, sentence |
| `pubmed_labels` | 1セクション1doc | pmid, label_id, label, text |

---

## アナライザー

全インデックスで **porter_stem** アナライザーを使用しています。

```
standard tokenizer → lowercase → porter_stem
```

`"running"` `"runs"` `"ran"` が同じ語幹 `"run"` にマッチします。  
`mesh`・`journal`・`label` 等の識別子フィールドは `keyword` 型（exact match）です。

---

## 検索例

```python
from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

res = es.search(
    index="pubmed_articles",
    body={
        "query": {
            "multi_match": {
                "query": "insulin resistance type 2 diabetes",
                "fields": ["title^2", "abstract"],
                "type": "best_fields"
            }
        },
        "size": 5
    }
)

for hit in res["hits"]["hits"]:
    print(hit["_source"]["pmid"], hit["_source"]["title"])
```

---

## 旧スクリプト (archive_prepare) との違い

| 項目 | 旧 (archive_prepare) | 新 (prepare_with_parquet) |
|---|---|---|
| データソース | SQLite (.db) | Parquet |
| 読み込み | メモリ全展開 | ストリーミング (iter_batches) |
| Bulk | シングルスレッド | parallel_bulk (4スレッド) |
| アナライザー | exact / stem の2種 | porter_stem に統一 |
| インデックス | article / sentence | article / sentence / label |
