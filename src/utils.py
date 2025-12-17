import hashlib

def hash_content(content):
    return hashlib.sha256(content.encode('utf-8')).hexdigest()