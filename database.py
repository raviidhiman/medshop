from pymongo import MongoClient
from datetime import datetime
from urllib.parse import quote_plus
import os

MONGO_USERNAME = ""
MONGO_PASSWORD = ""
MONGO_CLUSTER  = ""
DB_NAME        = "medshop"

username  = quote_plus(MONGO_USERNAME)
password  = quote_plus(MONGO_PASSWORD)
MONGO_URI = os.environ.get(
    "MONGO_URI",
    f"mongodb+srv://{username}:{password}@{MONGO_CLUSTER}/?retryWrites=true&w=majority&appName=medshop"
)


def get_db():
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]


def init_db():
    db = get_db()
    print("✅ MongoDB connected. Database ready.")
