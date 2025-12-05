import pymongo
import redis
from config import Config

# Initialize MongoDB connection
mongo_client = pymongo.MongoClient(Config.MONGO_URI, tlsAllowInvalidCertificates=True)
db = mongo_client.get_database("app")  # Automatically gets the DB from the URI
rental_collection = db["house_rental"] 
user_collection = db["users"] 

# Initialize Redis connection
redis_client = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=0, decode_responses=True)

def get_rental_info_by_ids(ids):
    """
    Fetch rental information based on a list of IDs.
    """
    # Assuming _id is stored as a string in the existing database
    return list(rental_collection.find({"_id": {"$in": ids}}))

def search_rentals(query_doc):
    """
    Execute a search query using the provided MongoDB query document.
    """
    result = list(rental_collection.find(query_doc))
    print(result)
    return result