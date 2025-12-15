import pymongo
from src.config import Config

# Initialize MongoDB connection
mongo_client = pymongo.MongoClient(Config.MONGO_URI, tlsAllowInvalidCertificates=True)
db = mongo_client.get_database("app")
user_collection = db["users"]