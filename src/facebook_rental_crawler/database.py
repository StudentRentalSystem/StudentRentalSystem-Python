from src.rag_service.rag import RagService

class Database:
    def __init__(self):
        self.rag_service = RagService()

    def get_database(self):
        return self.rag_service

database = Database().get_database()