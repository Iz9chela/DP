import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from backend.db.settings import MONGO_URI, DB_NAME

logger = logging.getLogger(__name__)

client: AsyncIOMotorClient = None
database: AsyncIOMotorDatabase = None

def init_db() -> None:
    """
    Initializes a singleton Motor client and database.
    This function should be called on application startup.
    """
    global client, database
    if client is None:
        client = AsyncIOMotorClient(MONGO_URI)
        database = client[DB_NAME]
        logger.info("Connected to MongoDB at %s, using DB: %s", MONGO_URI, DB_NAME)

def get_database() -> AsyncIOMotorDatabase:
    """
    Returns the global Motor database instance.
    If the database hasn't been initialized, it calls init_db().
    """
    if database is None:
        init_db()
    return database

def close_db() -> None:
    """
    Closes the Motor client.
    This function should be called on application shutdown.
    """
    global client
    if client is not None:
        client.close()
        logger.info("MongoDB client closed.")
