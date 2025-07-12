# Uses files to manage rate limiting wait times.
# Files are used because separate processes use different memory spaces,
# 	making it difficult to share the variables.

import time

filename = 'ratelimit_wait_time.txt'

def _load_ratelimit_wait_time():
	# Load the initial ratelimit wait time from a file or set it to 0.
	try:
		with open(filename) as f:
			return float(f.read().strip())
	except:
		return 0.0

def _write_ratelimit_wait_time(time_sec):
	# Write the current ratelimit wait time to a file.
	with open(filename, 'w') as f:
		f.write(str(time_sec))

def wait_for_rate_limit(time_sec):
	if time_sec <= 0:
		return 0
	time.sleep(time_sec)
	# If not interrupted, update the ratelimit wait time.
	ratelimit_wait = _load_ratelimit_wait_time() + time_sec
	_write_ratelimit_wait_time(ratelimit_wait)

def reset_ratelimit_wait_time():
	_write_ratelimit_wait_time(0.0)

def get_ratelimit_wait_time():
	return _load_ratelimit_wait_time()
