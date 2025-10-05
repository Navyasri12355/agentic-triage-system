# db/mongo_client.py
from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client[os.getenv("DB_NAME", "medusabytes")]
collection = db[os.getenv("COLLECTION", "patients_vitals")]

def insert_vitals(data: dict):
    collection.insert_one(data)
