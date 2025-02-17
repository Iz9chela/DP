import os
from backend.config.config import load_config
from backend.utils.path_utils import resolve_path

CONFIG_PATH = resolve_path("config.yaml")
config = load_config(CONFIG_PATH)

# For production, consider reading from environment variables:
MONGO_URI = os.getenv("MONGO_URI") or config["database"].get("uri", "mongodb+srv://{user}:{pass}@dp-database.fczwf.mongodb.net/?retryWrites=true&w=majority&appName=DP-Database")
DB_NAME = os.getenv("MONGO_DB_NAME") or config["database"].get("database_name", "dp_database")
