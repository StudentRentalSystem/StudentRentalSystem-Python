from src.rag_service.rag import RagService
from src.config import Config


class Database:
    def __init__(self):
        self.rag_service = RagService(
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

    def get_database(self):
        return self.rag_service

database = Database().get_database()