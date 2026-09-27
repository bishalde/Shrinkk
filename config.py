import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    MONGO_URI = os.getenv("MONGO_URI")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me")
