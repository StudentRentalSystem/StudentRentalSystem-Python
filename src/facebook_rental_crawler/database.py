# database.py
from pymongo import MongoClient, errors
from config import Config

class Database:
    def __init__(self):
        self.client = MongoClient(Config.DB_URL)
        self.db = self.client[Config.DB_NAME]
        self.collection = self.db[Config.DB_COLLECTION]

    def fetch_all_ids(self):
        # 只抓取 _id 欄位
        cursor = self.collection.find({}, {"_id": 1})
        return [str(doc["_id"]) for doc in cursor]

    def insert_post(self, post_document):
        try:
            self.collection.insert_one(post_document)
            print(f"✅ Post inserted: {post_document.get('_id', 'unknown')}")
        except errors.DuplicateKeyError:
            print("⚠️ Duplicate key found in database, skipping.")
        except Exception as e:
            print(f"❌ Error inserting to DB: {e}")

db_instance = Database()