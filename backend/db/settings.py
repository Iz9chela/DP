from backend.config.config import load_config
from backend.utils.path_utils import resolve_path

CONFIG_PATH = resolve_path("config.yaml")

# Load the configuration once.
_config = load_config(CONFIG_PATH)

# Expose MongoDB settings from the YAML configuration.
MONGO_URI = _config["database"]["uri"]
DB_NAME = _config["database"]["database_name"]
