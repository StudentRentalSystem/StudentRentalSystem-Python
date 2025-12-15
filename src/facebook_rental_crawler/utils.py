import hashlib
import json

def hash_content(content):
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def extract_json_from_string(text):
    try:
        # Find the first { and the last }
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            json_str = text[start:end+1]
            return json.loads(json_str)
        return None
    except json.JSONDecodeError:
        return None