# Elasticsearch + Apptainer 環境構築 README (Slurm/HPC 向け)

このドキュメントでは、

* Apptainer 上で Elasticsearch を起動する方法
* Python コンテナから Elasticsearch に接続する方法
* Slurm 環境での運用方法

について説明します。

本構成は HPC/研究クラスタ環境を想定しています。

---

# 構成概要

本構成では、

* Elasticsearch 用コンテナ
* Python 実行用コンテナ

を分離します。

```text
Node
├── elasticsearch.sif
├── A.sif (Python/uv)
├── scripts/
├── data/
└── project/
```

Elasticsearch は localhost:9200 で待ち受けます。

Python 側から localhost 経由で接続します。

---

# Requirements

必要要件:

* Linux
* Apptainer
* Slurm
* 8GB 以上の RAM 推奨

---

# ディレクトリ構成

```text
project/
├── README.md
├── sif/
│   ├── elasticsearch.sif
│   └── A.sif
├── scripts/
│   ├── build_es.sh
│   ├── run_es.sh
│   ├── shell_py.sh
│   └── stop_es.sh
├── data/
│   └── esdata/
└── .venv/
```

---

# 1. Elasticsearch 用 SIF 作成

## build_es.sh

```bash
#!/bin/bash

set -e

mkdir -p ../sif

apptainer build \
  ../sif/elasticsearch.sif \
  docker://docker.elastic.co/elasticsearch/elasticsearch:8.13.2
```

---

## 実行

```bash
cd scripts

chmod +x build_es.sh

./build_es.sh
```

生成物:

```text
sif/elasticsearch.sif
```

---

# 2. Elasticsearch 起動 script

## run_es.sh

```bash
#!/bin/bash

set -e

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)

ESDATA=${ROOT_DIR}/data/esdata

mkdir -p "${ESDATA}"

ulimit -n 65535

echo "[INFO] Starting Elasticsearch..."

apptainer exec \
  --cleanenv \
  --env discovery.type=single-node \
  --env xpack.security.enabled=false \
  --env ES_JAVA_OPTS="-Xms4g -Xmx4g" \
  --bind ${ESDATA}:/usr/share/elasticsearch/data \
  ${ROOT_DIR}/sif/elasticsearch.sif \
  /usr/local/bin/docker-entrypoint.sh eswrapper
```

---

# 3. Elasticsearch 停止

## stop_es.sh

```bash
#!/bin/bash

pkill -f elasticsearch
```

---

# 4. Python コンテナへ入る

## shell_py.sh

```bash
#!/bin/bash

set -e

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)

apptainer shell \
  --bind ${ROOT_DIR}:/workspace \
  ${ROOT_DIR}/sif/A.sif
```

---

# 5. Python 環境有効化

Python コンテナへ入った後:

```bash
cd /workspace

source .venv/bin/activate
```

---

# 6. Python package install

```bash
uv pip install elasticsearch pandas tqdm
```

または:

```bash
pip install elasticsearch pandas tqdm
```

---

# 7. Elasticsearch 接続確認

```python
from elasticsearch import Elasticsearch

es = Elasticsearch(
    "http://localhost:9200",
    request_timeout=60
)

print(es.info())
```

---

# 8. Elasticsearch 動作確認

別 shell から:

```bash
curl http://localhost:9200
```

正常時:

```json
{
  "tagline": "You Know, for Search"
}
```

---

# 9. Slurm 環境での注意

## Elasticsearch は compute node 上で起動する

Elasticsearch は login node ではなく compute node 上で動かしてください。

推奨:

```bash
srun --pty bash
```

または:

```bash
salloc
```

後に Elasticsearch を起動します。

---

# 10. vm.max_map_count 問題

Elasticsearch は:

```bash
vm.max_map_count=262144
```

を要求します。

確認:

```bash
sysctl vm.max_map_count
```

変更可能なら:

```bash
sudo sysctl -w vm.max_map_count=262144
```

ただし HPC 環境では sudo 不可な場合があります。

その場合は管理者に依頼してください。

---

# 11. 推奨 workflow

## shell 1

Elasticsearch 起動:

```bash
cd scripts

./run_es.sh
```

---

## shell 2

Python container:

```bash
cd scripts

./shell_py.sh
```

コンテナ内部:

```bash
cd /workspace

source .venv/bin/activate
```

---

# 12. Data 永続化

Elasticsearch data は:

```text
data/esdata
```

へ保存されます。

index を削除しない限り永続化されます。

---

# 13. Port

デフォルト:

```text
9200
```

使用中の場合は Elasticsearch が起動できません。

確認:

```bash
lsof -i:9200
```

---

# 14. メモリ設定

デフォルト:

```bash
-Xms4g -Xmx4g
```

メモリ不足時は run_es.sh を編集してください。

例:

```bash
--env ES_JAVA_OPTS="-Xms2g -Xmx2g"
```

---

# 15. 本構成の用途

本構成は以下用途を想定しています:

* Elasticsearch 検索基盤
* BM25 retrieval
* RAG retrieval
* PubMed retrieval
* knowledge retrieval
* scientific text search
* LLM backend retrieval

---

# 16. まとめ

本構成では:

* Apptainer 上で Elasticsearch を実行
* Python container から localhost 接続
* Slurm node 上で実行
* data 永続化対応

を実現しています。

HPC 環境において比較的安定して動作する構成です。
