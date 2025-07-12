import datetime
import os
import pytz

from irat.utils.settings import env

SERVER_ID = env('SERVER_ID')
log_filename = None
if SERVER_ID:
	log_filename = f'logs_{SERVER_ID}.txt'

def write_log(*args: str, **kwargs: str):
	print(*args, **kwargs)  # Print to console
	if log_filename:
		with open(log_filename, 'a') as f:
			print(*args, **kwargs, file=f)

ist = pytz.timezone('Asia/Kolkata')

def time_now():
	return datetime.datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S %Z')

def log_info(*args: str, **kwargs: str):
	write_log(f'{time_now()} [INFO]', *args, **kwargs)

def log_warning(*args: str, **kwargs: str):
	write_log(f'{time_now()} [WARNING]', *args, **kwargs)

def log_error(*args: str, **kwargs: str):
	write_log(f'{time_now()} [ERROR]', *args, **kwargs)

def log_debug(*args: str, **kwargs: str):
	write_log(*args, **kwargs)
