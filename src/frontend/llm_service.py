import requests
import json
import re
from config import Config
from ollama import Client

class LLMService:
    def __init__(self):
        self.api_url = f"{Config.LLM_SERVER_ADDRESS}:{Config.LLM_SERVER_PORT}/api/chat"
        self.model = Config.LLM_MODEL_NAME
        self.client = Client(
            host=f"{Config.LLM_SERVER_ADDRESS}",
            headers={'Authorization' : 'Bearer ' + Config.LLM_CLIENT_TOKEN}
        )
        
    def generate_mongo_query(self, user_input):
        """
        Convert natural language input into a MongoDB JSON query.
        """
        
        # System prompt instructs the LLM on how to map user intent to specific DB fields.
        # Note: The field names (e.g., "地址", "租金") MUST match the Chinese keys in the MongoDB.
        system_prompt = """
        You are a MongoDB query generator. Convert the user's rental requirements into a MongoDB find() JSON query.
        
        The database schema uses the following Chinese keys:
        - "地址" (String): Use regex for fuzzy search.
        - "租金.minRental", "租金.maxRental" (Int): Range query.
        - "格局.房", "格局.廳", "格局.衛" (Int): Exact match.
        - "坪數" (List[Float]): Match approximate range.
        - "性別限制.男", "性別限制.女" (Int): 1 means allowed.
        - "是否可養寵物", "是否可養魚", "是否可開伙", "是否有電梯", "是否有汽車停車位", "是否有機車停車位", "是否有頂樓加蓋" (Int): 1 for Yes, 0 for No.
        
        Return ONLY the JSON object. Do not include any explanations or markdown formatting.
        
        Example Input: "我要台南市 5000元以下的套房"
        Example Output: {"地址": {"$regex": "台南市"}, "租金.maxRental": {"$lte": 5000}, "格局.房": 1, "格局.廳": 0, "格局.衛": 1}
        """
        # headers = {
        #     "Content-Type": "application/json"
        # }
        
        # token = Config.LLM_CLIENT_TOKEN or Config.CLIENT_TOKEN
        # if token:
        #     headers["Authorization"] = f"Bearer {token}"
        #     print(f"🔑 Using token: {token[:4]}...{token[-4:] if len(token) > 8 else ''}")
        # else:
        #     print("⚠️ No LLM_CLIENT_TOKEN or CLIENT_TOKEN found in Config")
        
        model = self.model
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        # payload = {
        #     "model": self.model,
        #     "messages": [
        #         {"role": "system", "content": system_prompt},
        #         {"role": "user", "content": user_input}
        #     ],
        #     "stream": False,
        # }

        try:
            print(f"🤖 Calling LLM with: {user_input}")
            # response = requests.post(self.api_url, json=payload, headers=headers)
            # response.raise_for_status()
            response = self.client.chat(
                model=model,
                messages=messages,
                stream=False
            )
            content = response.json().get("message", {}).get("content", "")
            
            # Clean the response to ensure only valid JSON remains
            # Remove <think> tags if using models like Deepseek
            content = re.sub(r'(?s)<think>.*?</think>', '', content) 
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                print("❌ LLM did not return JSON")
                return None
                
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            return None