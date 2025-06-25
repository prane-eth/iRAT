import datetime

def now():
	return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def log_info(*args: str, **kwargs: str):
	print(f'{now()} [INFO]', *args, **kwargs)
	# args allow multiple arguments like log_info('hi', 'there', list1)

def log_warning(*args: str, **kwargs: str):
	print(f'{now()} [WARNING]', *args, **kwargs)

def log_error(*args: str, **kwargs: str):
	print(f'{now()} [ERROR]', *args, **kwargs)

def log_debug(*args: str, **kwargs: str):
	# print(f'{now()} [DEBUG]', *args)  # For debugging, we might not want the timestamp
	print(*args, **kwargs)

