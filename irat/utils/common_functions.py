import datetime

from irat.utils.logger import log_error, log_info


def user_message(content, role='user'):
	return {
		'role': role,
		'content': content
	}

def system_message(content):
	return user_message(content, role='system')

def assistant_message(content):
	return user_message(content, role='assistant')


def get_date():
	return datetime.datetime.now().strftime('%Y-%m-%d')

from multiprocessing import Process, Queue
import queue  # Needed to catch Empty exception

def run_with_timeout(func, args=(), timeout=30):
	q = Queue()  # Create a Queue object for inter-process communication
	# Create a process to execute the passed function, passing Queue and other *args, **kwargs as parameters
	p = Process(target=func, args=(q, *args))
	p.start()

	# Wait for the process to complete or time out
	try:
		# Try to get the result BEFORE joining the process
		result = q.get(timeout=timeout)
	except queue.Empty:
		log_info(f'function {func.__name__} Execution timed out ({timeout}s), terminating the process...')
		p.terminate()
		p.join()
		return None
	except Exception as e:
		log_error(f'Exception while getting result from queue: {e}')
		p.terminate()
		p.join()  # Make sure the process is terminated
		return None  # In case of timeout, we have no results

	p.join()
	return result
