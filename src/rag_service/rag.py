import chromadb
import hashlib
from chromadb import QueryResult, EmbeddingFunction
from chromadb.api import DefaultEmbeddingFunction
from chromadb.utils import embedding_functions

from src.config import Config
from src.facebook_rental_crawler.utils import hash_content
from src.rag_service.client import RemoteOllamaAuthEF


class RagConfig:
    tenant: str = Config.CHROMA_TENANT
    database: str = Config.CHROMA_DATABASE
    collection_name: str = Config.CHROMA_COLLECTION_NAME
    provider: str = Config.LLM_EMBEDDING_PROVIDER
    base_url: str = Config.LLM_EMBEDDING_SERVER_ADDRESS
    base_port: str = Config.LLM_EMBEDDING_SERVER_PORT
    model_type: str = Config.LLM_EMBEDDING_MODEL_TYPE
    embedding_token: str = Config.LLM_EMBEDDING_CLIENT_TOKEN
    chroma_token: str = Config.CHROMA_TOKEN


class RagService:
    _instance = None  # 類別層級的變數
    _initialized = False  # 防止重複執行 __init__

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(RagService, cls).__new__(cls)
        return cls._instance

    def __init__(self, rag_config: RagConfig = None):
        if rag_config is None:
            rag_config = RagConfig()

        self.client = chromadb.CloudClient(
            api_key=rag_config.chroma_token,
            tenant=rag_config.tenant,
            database=rag_config.database
        )

        self.embedding_function = self._get_embedding_function(rag_config.provider, rag_config.base_url, rag_config.base_port, rag_config.model_type, rag_config.embedding_token)

        actual_collection_name = f"{rag_config.collection_name}_{rag_config.model_type}"

        print(f"正在使用模型: {rag_config.model_type}")
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
