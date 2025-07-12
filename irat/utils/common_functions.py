from irat.utils.logger import log_debug
import datetime

import psutil
import signal
import socket


def user_message(content, role='user'):
	return {
		'role': role,
		'content': content
	}

def system_message(content):
	return user_message(content, role='system')

def assistant_message(content):
	return user_message(content, role='assistant')

def print_separator(text=None):
	if text:
		log_debug('-'*32, text, '-'*32)
		return
	log_debug('-' * 80)

def get_date():
	return datetime.datetime.now().strftime('%Y-%m-%d')

def get_date_month():
	return datetime.datetime.now().strftime('%Y-%m')

host = '0.0.0.0'

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
