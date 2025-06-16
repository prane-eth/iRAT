import datetime

def now():
	return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def log_info(*args: str):
	print(f'{now()} [INFO]', *args)
	# args allow multiple arguments like log_info('hi', 'there', list1)

def log_warning(*args: str):
	print(f'{now()} [WARNING]', *args)

def log_error(*args: str):
	print(f'{now()} [ERROR]', *args)

def log_debug(*args: str):
	# print(f'{now()} [DEBUG]', *args)
	print(*args)

