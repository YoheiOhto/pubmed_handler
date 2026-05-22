import glob
import json
import os
import sqlite3

import pandas as pd
from elasticsearch import Elasticsearch, helpers
from tqdm import tqdm

ES_HOST = "http://elasticsearch:9200" 
ES_PASSWORD = "micgm1Gemini" 
BULK_SIZE = 5000

INDEX_NAME = "pubmed_sentence"

MAPPING_BODY = {
  "settings": {
    "analysis": {
      "analyzer": {
        "english_exact": {
          "tokenizer": "standard",
          "filter": ["lowercase"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "PMID": { "type": "keyword" }, 
      "SENTID":        { "type": "keyword" },
      "SENTENCE":    { "type": "text", "analyzer": "english_exact" },
    }
  }
}

es = Elasticsearch(
    ES_HOST, 
    basic_auth=("elastic", ES_PASSWORD),
    request_timeout=60 
)

DB_DIR = "/workspace/99-NAS_data/pubmed/db"
db_files = glob.glob(os.path.join(DB_DIR, "pubmed_n25_*.db"))

def generate_actions(df, index_name):
    for row in df.itertuples(index=False):
        doc = row._asdict()
        yield {
            "_index": index_name,
            "_id": doc.get("SENTENCE_ID"), 
            "_source": doc
        }

print(f"\n2. Connecting to Elasticsearch and creating index: {INDEX_NAME}")
try:
    if es.indices.exists(index=INDEX_NAME):
        print(f"   -> Index '{INDEX_NAME}' already exists. Deleting...")
        es.indices.delete(index=INDEX_NAME)

    es.indices.create(index=INDEX_NAME, body=MAPPING_BODY)
    print(f"   -> Index '{INDEX_NAME}' created successfully with optimized mapping.")
except Exception as e:
    print(f"   -> Error creating index: {e}")
    exit()


for i, db_file in enumerate(tqdm(db_files)):
    try:
        conn = sqlite3.connect(db_file)
        df = pd.read_sql_query("SELECT * FROM sent_split", conn)
        conn.close()
        df = df.fillna("")
        
        num_records = len(df)
        successes, errors = helpers.bulk(
            es, 
            generate_actions(df, INDEX_NAME),
            chunk_size=BULK_SIZE,
            request_timeout=120 # タイムアウトをさらに延長
        )
        
        if errors:
            print(f"   -> WARNING: {len(errors)} errors encountered in this batch.")

    except Exception as e:
        print(f"   -> FATAL ERROR processing {os.path.basename(db_file)}: {e}")

print("\n--- Final Summary ---")
try:
    count_res = es.count(index=INDEX_NAME)
    print(f"Total unique documents in ES index '{INDEX_NAME}': {count_res['count']}")
except Exception as e:
    print(f"Error checking final document count: {e}")