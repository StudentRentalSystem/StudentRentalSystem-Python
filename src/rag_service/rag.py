import chromadb
import hashlib
from chromadb import QueryResult, EmbeddingFunction
from chromadb.api import DefaultEmbeddingFunction
from chromadb.utils import embedding_functions

from src.facebook_rental_crawler.utils import hash_content
from src.rag_service.client import RemoteOllamaAuthEF


class RagService:
    def __init__(self,
                 tenant: str,
                 database: str,
                 collection_name: str = "rent_posts",
                 provider: str = "ollama",
                 base_url: str = "http://localhost",
                 base_port: str = "11434",
                 model_type: str = "nomic-embed-text",
                 embedding_token: str = "",
                 chroma_token: str = ""):

        self.client = chromadb.CloudClient(
            api_key=chroma_token,
            tenant=tenant,
            database=database
        )

        self.embedding_function = self._get_embedding_function(provider, base_url, base_port, model_type, embedding_token)

        actual_collection_name = f"{collection_name}_{model_type}"

        print(f"正在使用模型: {model_type}")
        print(f"資料表名稱: {actual_collection_name}")

        self.collection = self.client.get_or_create_collection(
            name=actual_collection_name,
            embedding_function=self.embedding_function,
            # metadata={"hnsw:space": "cosine"}
        )

    def _get_embedding_function(self, provider: str, base_url: str, base_port: str, model_type: str, token: str) -> RemoteOllamaAuthEF | DefaultEmbeddingFunction:
        model_type = model_type.lower()

        if provider == "ollama":
            return RemoteOllamaAuthEF(
                base_url=f"{base_url}:{base_port}",
                api_key=token,
                model_name=model_type,
                timeout=120
            )

        elif provider == "default":
            return embedding_functions.DefaultEmbeddingFunction()

        else:
            raise ValueError(f"不支援的 provider: {provider}")

    def hash_content(self, content):
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def insert(self, raw_post: str, metadata: dict) -> str:
        new_id = hash_content(raw_post)
        self.collection.upsert(
            documents=[raw_post],
            metadatas=[metadata],
            ids=[new_id],
        )
        return new_id

    def query(self, question: str, filters: dict = None, n_results: int = 3) -> QueryResult:
        return self.collection.query(
            query_texts=[question],
            n_results=n_results,
            where=filters
        )
