import time
ratelimit_wait = 0

def wait_for_rate_limit(time_sec):
	global ratelimit_wait
	if time_sec > 0:
		time.sleep(time_sec)
		ratelimit_wait += time_sec
	return ratelimit_wait

def reset_ratelimit_wait_time():
	global ratelimit_wait
	ratelimit_wait = 0
	return ratelimit_wait
