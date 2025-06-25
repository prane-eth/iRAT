from irat.utils.logger import log_debug, log_error, log_info
import datetime
import requests
import subprocess
import time


def user_message(content, role='user'):
	return {
		'role': role,
		'content': content
	}

def system_message(content):
	return user_message(content, role='system')

def assistant_message(content):
	return user_message(content, role='assistant')

def print_separator():
	log_debug('-' * 80)

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

host = '0.0.0.0'

import psutil
import signal
import socket

def kill_process_on_port(port):
	for conn in psutil.net_connections(kind='tcp'):
		if conn.laddr and conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
			pid = conn.pid
			if pid is None:
				continue
			proc = psutil.Process(pid)
			proc.send_signal(signal.SIGTERM)
			proc.wait(timeout=15)
			return

def clear_port(port):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		s.bind((host, port))
	except OSError as e:
		if e.errno == 98:  # Address already in use
			log_debug(f'Clearing port {port}...')
			kill_process_on_port(port)
		else:
			raise
	finally:
		s.close()
