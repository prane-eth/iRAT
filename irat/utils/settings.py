# This Class is in charge of loading the settings from the .env file.

import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Settings:
        
    @classmethod
    def get(cls, key: str):
        return os.getenv(key)

def env(key: str, default=None):
    """
    Get the environment variable or return the default value if not set.
    """
    return os.getenv(key, default)
