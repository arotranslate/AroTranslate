import os

class Config:
    MODEL_LOAD_NAME = os.getenv("MODEL_LOAD_NAME", "NLLB-rup-ron-eng-ct2-v2")
    MAX_INPUT_TOKENS = int(os.getenv("MAX_INPUT_TOKENS", "1024"))
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "4"))
    MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "1024"))
    RATE_LIMIT = os.getenv("FLASK_RATE_LIMIT", "50 per minute")
    MEMCACHED_URI = os.getenv("MEMCACHED_URI") 
    if MEMCACHED_URI:
        STORAGE_URI = MEMCACHED_URI
    else:
        STORAGE_URI = "memory://"
    TALISMAN = bool(os.getenv("TALISMAN", "False") == "True")
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://mongodb:27017/")
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "arotranslate")
    DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME")
    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD")
    SECRET_KEY = os.getenv("SECRET_KEY")
