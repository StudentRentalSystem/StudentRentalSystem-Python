from src.config import Config
from src.rag_service.client import LLMClient, LLMConfig, LLMMode
from src.facebook_rental_crawler.prompts import PROMPT_TEMPLATE
from src.facebook_rental_crawler.database import database
import json


class RentalExtractor:
    def __init__(self):
        self.database = database

    @staticmethod
    def call_ollama(text: str) -> str:
        prompt = PROMPT_TEMPLATE.replace("{text}", text)
        config = LLMConfig(
            mode=LLMMode.CHAT,
            server_address=Config.LLM_SERVER_ADDRESS,
            server_port=Config.LLM_SERVER_PORT,
            model_type=Config.LLM_MODEL_TYPE,
            stream=False,
            token=Config.LLM_CLIENT_TOKEN,
        )
        client = LLMClient(config)
        response = client.call_local_model(prompt)
        return response

    def process_post_and_insert(self, raw_post: str) -> str:
        """
        Generate the metadata and uuid for the given post string, and
        store all of these into DB.        
        :param raw_post: The raw string of the post being processed.

        """
        metadata: dict = json.loads(self.call_ollama(raw_post))
        uuid: str = self.database.insert(raw_post, metadata)

        return uuid
