import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))

    PREFIX = "!"
    BOT_NAME = "ZELROVA"
    VERSION = "1.0 Foundation"

    DATABASE_TYPE = os.getenv("DATABASE_TYPE", "json")
    DATABASE_PATH = os.getenv("DATABASE_PATH", "data/database.json")

    SECURITY_ENABLED = os.getenv("SECURITY_ENABLED", "true").lower() == "true"
    AUTOMOD_ENABLED = os.getenv("AUTOMOD_ENABLED", "true").lower() == "true"
    TICKETS_ENABLED = os.getenv("TICKETS_ENABLED", "true").lower() == "true"
    LEVELS_ENABLED = os.getenv("LEVELS_ENABLED", "true").lower() == "true"
    AI_ENABLED = os.getenv("AI_ENABLED", "true").lower() == "true"