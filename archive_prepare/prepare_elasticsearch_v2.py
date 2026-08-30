import glob
import os
import sqlite3

import pandas as pd
from elasticsearch import Elasticsearch, helpers
from tqdm import tqdm

# --- 設定 ---
ES_HOST = "http://elasticsearch:9200"
ES_PASSWORD = "micgm1Gemini"
DB_DIR = "/workspace/0-utils/1-data/pubmed/db/"
BULK_SIZE = 5000

# インデックス名を v2 に変更
INDEX_NAME = "pubmed_sentence_v2"

# 新しいマッピング定義（Porter Stemmerを使用）
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

# --- Elasticsearch接続 ---
es = Elasticsearch(
    ES_HOST, 
    basic_auth=("elastic", ES_PASSWORD),
    request_timeout=60 
)

# DBファイルの取得
db_files = glob.glob(os.path.join(DB_DIR, "pubmed_n25_*.db"))

# バルクインサート用のアクション生成関数
def generate_actions(df, index_name):
    # pandasのitertuplesは高速です
    for row in df.itertuples(index=False):
        doc = row._asdict()
        yield {
            "_index": index_name,
            # DBのカラム名に SENTENCE_ID がある前提です
            "_id": doc.get("SENTENCE_ID"), 
            "_source": doc
        }

# --- メイン処理 ---
print(f"\nProcessing Index: {INDEX_NAME}")

try:
    # 1. 既存インデックスの確認と削除
    if es.indices.exists(index=INDEX_NAME):
        print(f" -> Index '{INDEX_NAME}' already exists. Deleting...")
        es.indices.delete(index=INDEX_NAME)
    
    # 2. 新しい設定でインデックスを作成
    es.indices.create(index=INDEX_NAME, body=MAPPING_BODY)
    print(f" -> Index '{INDEX_NAME}' created successfully with stemmed mapping.")

except Exception as e:
    print(f" -> Error during index creation: {e}")
    exit()

# 3. データの投入ループ
print(f" -> Found {len(db_files)} database files.")

for i, db_file in enumerate(tqdm(db_files)):
    try:
        conn = sqlite3.connect(db_file)
        # SQLiteからデータを取得
        df = pd.read_sql_query("SELECT * FROM sent_split", conn)
        conn.close()
        
        # NaNを空文字に置換（ESのエラー防止）
        df = df.fillna("")
        
        # バルクインサート実行
        successes, errors = helpers.bulk(
            es, 
            generate_actions(df, INDEX_NAME),
            chunk_size=BULK_SIZE,
            request_timeout=120
        )
        
        if errors:
            print(f" -> WARNING: {len(errors)} errors encountered in {os.path.basename(db_file)}.")

    except Exception as e:
        print(f" -> FATAL ERROR processing {os.path.basename(db_file)}: {e}")

# --- 最終確認 ---
print("\n--- Final Summary ---")
try:
    es.indices.refresh(index=INDEX_NAME) # カウントを正確にするためリフレッシュ
    count_res = es.count(index=INDEX_NAME)
    print(f"Total documents in '{INDEX_NAME}': {count_res['count']}")
except Exception as e:
    print(f"Error checking final document count: {e}")