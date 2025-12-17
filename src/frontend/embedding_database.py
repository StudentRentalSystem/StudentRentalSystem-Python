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

    def get_rental_info_by_ids(self, ids: list[str]) -> list:
        """
        Fetch rental information based on a list of IDs.
        """
        # Assuming _id is stored as a string in the existing database
        if (ids is None) or (len(ids) == 0):
            return []
        query_result = self.embedding_database.collection.get(
            ids=ids,
            include=["documents", "metadatas"]
        )
        if (query_result is None) or (len(query_result) == 0):
            return []

        metadatas = query_result['metadatas']
        documents = query_result['documents']

        results = [
            {"metadata": m, "document": d}
            for d, m in zip(documents, metadatas)
        ]

        return results

    def search_rentals(self, query: str) -> list:
        """
        Execute a search query using the provided MongoDB query document.
        """
        query_constraints = self.query_generator.format_query(query)
        """
        The output format of query_constraints is:
        {
            "$and": [
              {"address": {"$in": ["凱旋路"]}}, // 或是讓語意搜尋處理 address，這裡 filter 留空也可以，看策略
              {"gender_restriction": {"$in": [0, 2]}} // 女生可以租「不限」或「限女」
            ]
        }
        """
        if (query is None) or (len(query) == 0):
           return []

        query_result = self.embedding_database.collection.query(
            query_texts=[query],
            include=["documents", "metadatas"],
            where=query_constraints
        )

        if (query_result is None) or (len(query_result) == 0):
            return []

        """
        The results will be:
        {
            "ids": ['a', 'b', 'c', ...]
            "metadatas": ['a', 'b', 'c', ...]
            "documents": ['a', 'b', 'c', ...]
        }
        """
        metadatas = [item for batch in query_result['metadatas'] for item in batch]
        documents = [item for batch in query_result['documents'] for item in batch]
        ids = [i for batch in query_result["ids"] for i in batch]

        results = [
            {'id': i, 'metadata': m, 'document': d}
            for i, m, d in zip(ids, metadatas, documents)
        ]
        return results