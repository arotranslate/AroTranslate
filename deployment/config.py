import os

class Config:
    MODEL_LOAD_NAME = os.getenv("MODEL_LOAD_NAME", "NLLB-rup-ron-eng-ct2-v2")
    MAX_INPUT_TOKENS = int(os.getenv("MAX_INPUT_TOKENS", "1024"))
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "4"))
    MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "1024"))
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False") == "True"
    RATE_LIMIT = os.getenv("FLASK_RATE_LIMIT", "50 per minute")
    MEMCACHED_HOST = os.getenv("MEMCACHED_HOST", "localhost")
    MEMCACHED_PORT = int(os.getenv("MEMCACHED_PORT", 11211))
    MEMCACHED = f'{MEMCACHED_HOST}:{MEMCACHED_PORT}'
    TALISMAN = bool(os.getenv("TALISMAN", "False") == "True")