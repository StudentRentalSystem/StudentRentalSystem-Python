from src.rag_service.rag import RagService
from src.config import Config

# Initialize MongoDB connection
# mongo_client = pymongo.MongoClient(Config.MONGO_URI, tlsAllowInvalidCertificates=True)
# db = mongo_client.get_database("app")  # Automatically gets the DB from the URI
# rental_collection = db["house_rental"]
# user_collection = db["users"]
#
# # Initialize Redis connection
# redis_client = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=0, decode_responses=True)
database = RagService(
    tenant=Config.CHROMA_TENANT,
    database=Config.CHROMA_DATABASE,
    collection_name=Config.CHROMA_COLLECTION_NAME,
    provider=Config.LLM_EMBEDDING_PROVIDER,
    base_url=Config.LLM_EMBEDDING_SERVER_ADDRESS,
    base_port=Config.LLM_EMBEDDING_SERVER_PORT,
    model_type=Config.LLM_EMBEDDING_MODEL_TYPE,
    embedding_token=Config.LLM_EMBEDDING_CLIENT_TOKEN,
    chroma_token=Config.CHROMA_TOKEN,
)

def get_rental_info_by_ids(ids):
    """
    Fetch rental information based on a list of IDs.
    """
    # Assuming _id is stored as a string in the existing database
    return list(
        database.collection.get(
            ids=ids,
            include=["documents", "metadatas"]
        )
    )

def search_rentals(query_doc):
    """
    Execute a search query using the provided MongoDB query document.
    """
    result = list(rental_collection.find(query_doc))
    print(result)
    return result