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
	value = os.getenv(key, default)
	if value is None:
		return value
	if isinstance(value, str):
		value = value.strip()
		if value.lower() in ('true', 'false'):
			return value.lower() == 'true'
		if not value:
			return None
	return value

def set_env(key: str, value: str):
	# Set the environment variable.
	os.environ[key] = value
