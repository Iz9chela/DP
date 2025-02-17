import logging
from pymongo import MongoClient
from backend.services.settings import MONGO_URI, DB_NAME

logger = logging.getLogger(__name__)

client = None
db = None

def init_db():
    global client, db
    if client is None:
        try:
            client = MongoClient(MONGO_URI)
            db = client[DB_NAME]
            logger.info("Connected to MongoDB at %s, using DB: %s", MONGO_URI, DB_NAME)
        except Exception as e:
            logger.error("Could not connect to MongoDB: %s", e)
            raise

def get_db():
    """
    Returns a reference to the MongoDB database.
    Initializes the connection if it hasn't been created yet.
    """
    global db
    if db is None:
        init_db()
    return db

