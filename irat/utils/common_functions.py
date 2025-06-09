
def user_message(content, role='user'):
	return {
		'role': role,
		'content': content
	}

def system_message(content):
	return user_message(content, role='system')

def assistant_message(content):
	return user_message(content, role='assistant')
