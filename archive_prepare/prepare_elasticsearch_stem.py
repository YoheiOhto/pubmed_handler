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

# ==========================
# New Mapping (your version)
# ==========================
MAPPING_BODY = {
  "settings": {
    "analysis": {
      "analyzer": {
        "my_english_stemmed": { 
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "porter_stem"
          ]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "PMID": { "type": "keyword" },
      "SENTID": { "type": "keyword" },
      "SENTENCE": { 
          "type": "text", 
          "analyzer": "my_english_stemmed"
      }
    }
  }
}

print(json.dumps(MAPPING_BODY, indent=2))

# =============================
# Connect to Elasticsearch
# =============================
es = Elasticsearch(
    ES_HOST,
    basic_auth=("elastic", ES_PASSWORD),
    request_timeout=60
)

DB_DIR = "/workspace/99-NAS_data/pubmed/db"
db_files = glob.glob(os.path.join(DB_DIR, "pubmed_n25_*.db"))

# =============================
# Helper: Bulk action generator
# =============================
def generate_actions(df, index_name):
    for row in df.itertuples(index=False):
        doc = row._asdict()
        yield {
            "_index": index_name,
            "_id": doc.get("SENTID"),   # ← ここを統一
            "_source": doc
        }

# =============================
# Create index
# =============================
print(f"\n2. Connecting to Elasticsearch and creating index: {INDEX_NAME}")

try:
    if es.indices.exists(index=INDEX_NAME):
        print(f"   -> Index '{INDEX_NAME}' already exists. Deleting…")
        es.indices.delete(index=INDEX_NAME)

    print("   -> Creating index with mapping...")
    es.indices.create(index=INDEX_NAME, body=MAPPING_BODY)
    print("   -> Index created successfully.")

except Exception as e:
    print("   -> ERROR creating index:")
    if hasattr(e, "info"):
        print(json.dumps(e.info, indent=2))
    else:
        print(e)
    exit()

# =============================
# Bulk import
# =============================
print("\n3. Starting bulk insert...\n")

for db_file in tqdm(db_files):
    try:
        conn = sqlite3.connect(db_file)
        df = pd.read_sql_query("SELECT * FROM sent_split", conn)
        conn.close()
        df = df.fillna("")

        try:
            successes, errors = helpers.bulk(
                es,
                generate_actions(df, INDEX_NAME),
                chunk_size=BULK_SIZE,
                request_timeout=120
            )
        except Exception as bulk_err:
            print(f"   -> BULK ERROR in {db_file}: {bulk_err}")
            continue

        if errors:
            print(f"   -> Warning: {len(errors)} errors in batch.")

    except Exception as e:
        print(f"   -> FATAL ERROR processing {os.path.basename(db_file)}: {e}")

# =============================
# Final Count Check
# =============================
print("\n--- Final Summary ---")
try:
    count_res = es.count(index=INDEX_NAME)
    print(f"Total documents in '{INDEX_NAME}': {count_res['count']}")
except Exception as e:
    print(f"Error when counting index documents: {e}")
