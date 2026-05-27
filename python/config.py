from pathlib import Path
from typing import Dict

from dotenv import load_dotenv
import os


BASE_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BASE_DIR / ".env"


def load_db_config(database_required: bool = True) -> Dict[str, object]:
    load_dotenv(ENV_PATH)

    config = {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
    }

    database = os.getenv("DB_NAME")
    if database:
        config["database"] = database
    elif database_required:
        raise ValueError("DB_NAME is missing from .env")

    return config

