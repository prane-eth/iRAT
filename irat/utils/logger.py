import datetime

def log_info(message: str):
	print(f'{datetime.now()} [INFO] {message}')

def log_warning(message: str):
	print(f'{datetime.now()} [WARNING] {message}')

def log_error(message: str):
	print(f'{datetime.now()} [ERROR] {message}')
