# extractor.py
import requests
import json
import re
from config import Config
from utils import extract_json_from_string, hash_content

# 將 extract_prompt.txt 完整內容填入
PROMPT_TEMPLATE = """請根據以下租屋貼文，轉換為指定的 JSON 格式。所有欄位皆為字串、列表或數值，請務必完整填入。

【輸出 JSON 欄位格式（必填）】
請嚴格使用以下欄位與結構，不可新增、刪除或更改欄位名稱：
{
  "地址": "市區路地址",
  "租金": {"maxRental": 0, "minRental": 0},
  "坪數": [],
  "格局": {"房":0, "廳":0, "衛":0},
  "性別限制": {"男": 0, "女": 0},
  "是否可養寵物": -1,
  "是否可養魚": -1,
  "是否可開伙": -1,
  "是否有電梯": -1,
  "是否可租屋補助": -1,
  "是否有頂樓加蓋": -1,
  "是否有機車停車位": -1,
  "是否有汽車停車位": -1,
  "聯絡方式": [
    {
      "聯絡人": "name",
      "手機": ["手機號碼"],
      "lineID": ["line ID"],
      "lineLink": ["line 連結"],
      "others": ["其他聯絡方式"]
    }
  ],
  "照片": []
}

【欄位擷取規則】

地址：必須包含「市」、「區」、「路/街」，例如「台南市東區勝利路25號」。

租金：int 格式，如貼文出現單一租金，則 minRental = maxRental；如出現租金範圍，則分別取最小與最大值。

坪數：

擷取「數字+坪」的格式，僅保留數字（float），排除與格局無關或非正確格式者。

排除以下內容：格局（如「4房2廳2衛」）、間數（如「6間」）、郵遞區號（如「701」、「114」）。

大於等於 100 坪或無法辨識的內容請填入 -1。

格局：擷取房、廳、衛數量（缺漏者補 0），例：{"房":3,"廳":1,"衛":2}。

性別限制：

若限女性則 "女": 1, "男": 0；

若限男性則 "男": 1, "女": 0；

若不限或未知則皆為 0。

是否可養寵物 / 養魚 / 開伙 / 有電梯：若明確提到允許，填 1；若明確禁止，填 0；未提及，填 -1。

是否可租屋補助 / 有頂樓加蓋 / 有機車停車位 / 有汽車停車位：若提及則填 1 或 0，否則為 -1。

聯絡方式：

若有多位聯絡人，請全部列出為多個 JSON 物件。

聯絡人：若未提及，填空字串 ""。

手機: 僅擷取貼文中出現的台灣手機號碼，若貼文中未出現，請填空陣列 []，嚴禁捏造或補足格式化手機號碼

lineID：如與手機相同，也應填入手機欄；如未提供，填空陣列。

lineLink：提供的 Line 連結；如無，填空陣列。

others：如「私訊我」、「留言聯絡」等非明確管道。

照片：若貼文中出現圖片連結，擷取網址作為清單，否則填空陣列 []。

【重要限制】

僅回傳 一筆完整 JSON 結果。

嚴格遵守欄位與格式，JSON 結構必須可直接解析（例如 Python JSON parser 或 JavaScript JSON.parse()）。

不附加任何文字說明、錯誤提示或註解，僅回傳 JSON 結果本身。

貼文內容如下：
{text}
"""

class RentalExtractor:
    def __init__(self):
        # 處理 URL 結尾斜線問題，確保路徑正確
        base_url = Config.LLM_SERVER_ADDRESS.rstrip('/')
        if not base_url.startswith('http'):
             # 假設 Config 只有 IP 或 Domain
             self.api_url = f"http://{base_url}:{Config.LLM_SERVER_PORT}/api/chat"
        else:
             # 假設 Config 已經是完整 URL
             self.api_url = f"{base_url}/api/chat"
             
        self.model = Config.LLM_MODEL_TYPE

    def call_ollama(self, text):
        prompt = PROMPT_TEMPLATE.replace("{text}", text)
        
        # 設定 Headers (包含 Authorization)
        headers = {
            "Content-Type": "application/json"
        }
        
        # 檢查 Config 是否有 TOKEN，如果有才加入
        if hasattr(Config, 'LLM_CLIENT_TOKEN') and Config.LLM_CLIENT_TOKEN:
             headers["Authorization"] = f"Bearer {Config.LLM_CLIENT_TOKEN}"
        elif hasattr(Config, 'LLM_API_KEY') and Config.LLM_API_KEY:
             headers["Authorization"] = f"Bearer {Config.LLM_API_KEY}"

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
        
        try:
            # 修正重點：headers 必須作為參數傳遞，不能放在 payload 裡面
            response = requests.post(self.api_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json().get("message", {}).get("content", "")
        except Exception as e:
            print(f"❌ LLM Call Error: {e}")
            # 如果是 401/403，特別印出提示
            if isinstance(e, requests.exceptions.HTTPError):
                if e.response.status_code in [401, 403]:
                    print("⚠️ 權限錯誤：請檢查 .env 檔案中的 LLM_CLIENT_TOKEN 或 CLIENT_TOKEN 是否正確。")
            return ""

    def process_post(self, raw_post):
        attempts = 0
        success = False
        processed_data = None

        print(f"🔍 Processing post...")
        
        while attempts < Config.RETRY_ATTEMPTS and not success:
            llm_response = self.call_ollama(raw_post)
            # 移除 <think> 標籤 (針對 deepseek 或其他有思考過程的模型)
            clean_response = re.sub(r'(?s)<think>.*?</think>', '', llm_response).strip()
            
            json_obj = extract_json_from_string(clean_response)
            
            if json_obj:
                try:
                    self._normalize_data(json_obj)
                    json_obj["_id"] = hash_content(raw_post)
                    processed_data = json_obj
                    success = True
                except Exception as e:
                    print(f"⚠️ Data Normalization Error: {e}")
                    attempts += 1
            else:
                print("⚠️ Failed to parse JSON from LLM response")
                attempts += 1
                
        return processed_data

    def _normalize_data(self, data):
        # 修正坪數
        if "坪數" in data:
            data["坪數"] = [-1 if x >= 100 else x for x in data["坪數"]]
        
        # 修正聯絡方式結構 (對應 RentalExtractor.java 的 formSameJSON)
        if "聯絡方式" in data:
            new_contacts = []
            for contact in data["聯絡方式"]:
                normalized = {
                    "聯絡人": contact.get("聯絡人", "") if contact.get("聯絡人") != "未知" else "",
                    "手機": self._clean_list(contact.get("手機")),
                    "lineID": self._clean_list(contact.get("lineID")),
                    "lineLink": self._clean_list(contact.get("lineLink")),
                    "others": self._clean_list(contact.get("others"))
                }
                # 去除手機號碼中的橫線
                normalized["手機"] = [p.replace("-", "") for p in normalized["手機"]]
                new_contacts.append(normalized)
            data["聯絡方式"] = new_contacts

    def _clean_list(self, val):
        # 對應 checkFirstObject 邏輯
        if not val: return []
        if isinstance(val, list) and len(val) == 1 and (not val[0] or val[0] == "未知"):
            return []
        return val if isinstance(val, list) else []