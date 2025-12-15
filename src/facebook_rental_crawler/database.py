from src.rag_service.rag import RagService
from src.config import Config


class Database:
    def __init__(self):
        self.rag_service = RagService()

    def get_database(self):
        return self.rag_service

database = Database().get_database()