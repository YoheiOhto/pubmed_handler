'''
 # @ Author: Yohei Ohto
 # @ Create Time: 2026-05-21
 # @ Description:
 #   PubMed parquet -> Elasticsearch (porter_stem, BM25)
 #
 #   インデックス:
 #     pubmed_articles  : 1記事1doc (pmid, title, abstract, journal, year, mesh, pub_type)
 #     pubmed_sentences : 1文1doc   (pmid, sent_id, sentence)
 #     pubmed_labels    : 1セクション1doc (pmid, label_id, label, text)
'''

import os
from pathlib import Path

import pyarrow.parquet as pq
from dotenv import load_dotenv
from elasticsearch import Elasticsearch, helpers
from tqdm import tqdm

load_dotenv()

# =========================================================
# Config
# =========================================================

ES_HOST     = os.environ.get("ES_HOST", "http://elasticsearch:9200")
ES_USER     = os.environ.get("ES_USER", "elastic")
ES_PASSWORD = os.environ.get("ES_PASSWORD", "")
BULK_SIZE   = 5_000

DATA_DIR = Path(os.environ.get("DATA_DIR", "."))
PUBMED_DIR = DATA_DIR / "260420_pubmed"

ARTICLE_PARQUET  = PUBMED_DIR / "combined_articles.parquet"
SENTENCE_PARQUET = PUBMED_DIR / "combined_sentences.parquet"
LABEL_PARQUET    = PUBMED_DIR / "combined_labels.parquet"

INDEX_ARTICLE  = "pubmed_articles"
INDEX_SENTENCE = "pubmed_sentences"
INDEX_LABEL    = "pubmed_labels"


# =========================================================
# Analyzer (porter_stem)
# =========================================================

STEMMED_ANALYZER = {
    "analysis": {
        "analyzer": {
            "english_stemmed": {
                "tokenizer": "standard",
                "filter": ["lowercase", "porter_stem"],
            }
        }
    }
}

# =========================================================
# Mappings
# =========================================================

MAPPING_ARTICLE = {
    "settings": STEMMED_ANALYZER,
    "mappings": {
        "properties": {
            "pmid":             {"type": "long"},
            "title":            {"type": "text", "analyzer": "english_stemmed"},
            "abstract":         {"type": "text", "analyzer": "english_stemmed"},
            "journal":          {"type": "keyword"},
            "language":         {"type": "keyword"},
            "year":             {"type": "integer"},
            "mesh":             {"type": "keyword"},
            "publication_types":{"type": "keyword"},
            "abstract_truncated":{"type": "integer"},
        }
    },
}

MAPPING_SENTENCE = {
    "settings": STEMMED_ANALYZER,
    "mappings": {
        "properties": {
            "pmid":     {"type": "long"},
            "sent_id":  {"type": "integer"},
            "sentence": {"type": "text", "analyzer": "english_stemmed"},
        }
    },
}

MAPPING_LABEL = {
    "settings": STEMMED_ANALYZER,
    "mappings": {
        "properties": {
            "pmid":     {"type": "long"},
            "label_id": {"type": "integer"},
            "label":    {"type": "keyword"},
            "text":     {"type": "text", "analyzer": "english_stemmed"},
        }
    },
}


# =========================================================
# Helpers
# =========================================================

def make_es():
    return Elasticsearch(
        ES_HOST,
        basic_auth=(ES_USER, ES_PASSWORD),
        request_timeout=60,
    )


def create_index(es, index_name, mapping):
    if es.indices.exists(index=index_name):
        print(f"  Index '{index_name}' exists → deleting")
        es.indices.delete(index=index_name)
    es.indices.create(index=index_name, body=mapping)
    print(f"  Index '{index_name}' created")


def bulk_index(es, actions_iter, index_name, total):
    success, failed = 0, 0
    for ok, info in helpers.parallel_bulk(
        es,
        actions_iter,
        chunk_size=BULK_SIZE,
        thread_count=4,
        raise_on_error=False,
    ):
        if ok:
            success += 1
        else:
            failed += 1
    print(f"  {index_name}: indexed={success}, failed={failed}")


# =========================================================
# Action generators
# =========================================================

def article_actions(parquet_path, index_name):
    pf = pq.ParquetFile(parquet_path)
    for batch in pf.iter_batches(batch_size=BULK_SIZE):
        df = batch.to_pydict()
        n = len(df["pmid"])
        for i in range(n):
            yield {
                "_index": index_name,
                "_id":    df["pmid"][i],
                "_source": {
                    "pmid":              df["pmid"][i],
                    "title":             df["title"][i] or "",
                    "abstract":          df["abstract"][i] or "",
                    "journal":           df["journal"][i] or "",
                    "language":          df["language"][i] or "",
                    "year":              df["year"][i],
                    "mesh":              df["mesh"][i] or [],
                    "publication_types": df["publication_types"][i] or [],
                    "abstract_truncated":df["abstract_truncated"][i],
                },
            }


def sentence_actions(parquet_path, index_name):
    pf = pq.ParquetFile(parquet_path)
    for batch in pf.iter_batches(batch_size=BULK_SIZE):
        df = batch.to_pydict()
        n = len(df["pmid"])
        for i in range(n):
            pmid    = df["pmid"][i]
            sent_id = df["sent_id"][i]
            yield {
                "_index": index_name,
                "_id":    f"{pmid}_{sent_id}",
                "_source": {
                    "pmid":     pmid,
                    "sent_id":  sent_id,
                    "sentence": df["sentence"][i] or "",
                },
            }


def label_actions(parquet_path, index_name):
    pf = pq.ParquetFile(parquet_path)
    for batch in pf.iter_batches(batch_size=BULK_SIZE):
        df = batch.to_pydict()
        n = len(df["pmid"])
        for i in range(n):
            pmid     = df["pmid"][i]
            label_id = df["label_id"][i]
            yield {
                "_index": index_name,
                "_id":    f"{pmid}_{label_id}",
                "_source": {
                    "pmid":     pmid,
                    "label_id": label_id,
                    "label":    df["label"][i] or "",
                    "text":     df["text"][i] or "",
                },
            }


# =========================================================
# Main
# =========================================================

if __name__ == "__main__":

    es = make_es()
    print(f"Connected: {es.info()['version']['number']}\n")

    tasks = [
        ("ARTICLES",  INDEX_ARTICLE,  MAPPING_ARTICLE,  ARTICLE_PARQUET,  article_actions),
        ("SENTENCES", INDEX_SENTENCE, MAPPING_SENTENCE, SENTENCE_PARQUET, sentence_actions),
        ("LABELS",    INDEX_LABEL,    MAPPING_LABEL,    LABEL_PARQUET,    label_actions),
    ]

    for label, index_name, mapping, parquet_path, gen_fn in tasks:
        print(f"{'='*60}")
        print(f"{label}: {parquet_path.name}")
        print(f"{'='*60}")

        if not parquet_path.exists():
            print(f"  [SKIP] {parquet_path} not found\n")
            continue

        meta = pq.read_metadata(parquet_path)
        print(f"  rows: {meta.num_rows:,}")

        create_index(es, index_name, mapping)
        bulk_index(es, gen_fn(parquet_path, index_name), index_name, meta.num_rows)

        es.indices.refresh(index=index_name)
        count = es.count(index=index_name)["count"]
        print(f"  Final count: {count:,}\n")

    print("All done!")
