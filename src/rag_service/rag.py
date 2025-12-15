import json
import chromadb
import os
import uuid
from chromadb.utils import embedding_functions


class RagService:
    def __init__(self,
                 db_path: str = "./rent_db",
                 collection_name: str = "rent_posts",
                 model_type: str = "nomic"):  # 新增這個參數來選擇模型

        self.client = chromadb.PersistentClient(path=db_path)

        # 1. 取得對應的 Embedding Function
        self.ef = self._get_embedding_function(model_type)

        # 2. 建立 Collection (把 ef 傳進去，Chroma 就會自動用它來算向量)
        # 注意：建議 Collection 名稱最好跟著模型走，避免混用
        actual_collection_name = f"{collection_name}_{model_type}"

        print(f"正在使用模型: {model_type}")
        print(f"資料表名稱: {actual_collection_name}")

        self.collection = self.client.get_or_create_collection(
            name=actual_collection_name,
            embedding_function=self.ef
        )

    def _get_embedding_function(self, model_type: str):
        """
        根據輸入的 model_type 回傳對應的 Chroma Embedding Function
        """
        model_type = model_type.lower()

        # A. 本地 Ollama (推薦：nomic-embed-text)
        if model_type == "nomic":
            return embedding_functions.OllamaEmbeddingFunction(
                url="http://localhost:11434/api/embeddings",
                model_name="nomic-embed-text"  # 確保你有 pull 這個
            )

        # B. OpenAI (最強大，但要錢)
        elif model_type == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("使用 OpenAI 模式請先設定環境變數 OPENAI_API_KEY")

            return embedding_functions.OpenAIEmbeddingFunction(
                api_key=api_key,
                model_name="text-embedding-3-small"
            )

        # C. Chroma 預設 (all-MiniLM-L6-v2)
        # 優點：不用安裝 Ollama 也不用錢，適合測試，但對中文較弱
        elif model_type == "default":
            return embedding_functions.DefaultEmbeddingFunction()

        else:
            raise ValueError(f"不支援的模型類型: {model_type}")

    def insert(self, raw_post: str, metadata: dict):
        new_id = str(uuid.uuid4())
        self.collection.upsert(
            documents=[raw_post],
            metadatas=[metadata],
            ids=[new_id],
        )
        return new_id

    def query(self, question: str, filters: dict = None, n_results: int = 3):
        return self.collection.query(
            query_texts=[question],
            n_results=n_results,
            where=filters
        )
