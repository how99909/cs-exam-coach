import os


API_BASE_URL = os.getenv(
    "API_BASE_URL", 
    "http://localhost:8000"
)

DEFAULT_API_TIMEOUT = 30