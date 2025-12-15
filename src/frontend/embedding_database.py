from src.config import Config
from src.query_generator.query_generator import MiniRagApp
from src.rag_service.llm_config import LLMConfig, LLMMode
from src.rag_service.rag import RagService

class EmbeddingDatabase:
    def __init__(self):
        self.embedding_database =   RagService()
        self.llm_config = LLMConfig(
            mode=LLMMode.CHAT,
            server_address=Config.LLM_SERVER_ADDRESS,
            server_port=Config.LLM_SERVER_PORT,
            model_type=Config.LLM_MODEL_TYPE,
            stream=False
        )
        self.query_generator = MiniRagApp(self.llm_config)

    def get_rental_info_by_ids(self, ids: str):
        """
        Fetch rental information based on a list of IDs.
        """
        # Assuming _id is stored as a string in the existing database
        return list(
            self.embedding_database.collection.get(
                ids=ids,
                include=["documents", "metadatas"]
            )
        )

    def search_rentals(self, query: str):
        """
        Execute a search query using the provided MongoDB query document.
        """
        query_constraints = self.query_generator.format_query(query)
        result = list(self.embedding_database.collection.query(
            query_texts=[query],
            include=["documents", "metadatas"],
            where=query_constraints
        ))
        print(result)
        return result