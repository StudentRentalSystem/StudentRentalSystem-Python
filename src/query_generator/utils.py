import json
from typing import Optional, Dict, Any


def get_string_json(text: str) -> Optional[Dict[str, Any]]:
    """
    從字串中尋找並提取第一個 JSON 物件 ({...})
    """
    try:
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1:
            return None

        json_str = text[start: end + 1]
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None