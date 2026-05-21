import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app

app = create_app()
app.config['WTF_CSRF_ENABLED'] = False
client = app.test_client()

# Login as default admin (created at app init)
login_resp = client.post('/auth/login', data={'username': 'admin', 'password': 'admin123', 'remember_me': 'y'}, follow_redirects=True)
print('Login status:', login_resp.status_code)

resp = client.post('/ip-detection/analyze', json={'ip': 'not-an-ip', 'use_cache': True}, follow_redirects=False)
print('Invalid IP - Status code:', resp.status_code)
try:
	print('JSON:', resp.get_json())
except Exception as e:
	print('JSON parse error:', e)

resp2 = client.post('/ip-detection/analyze', json={'ip': '8.8.8.8', 'use_cache': True}, follow_redirects=False)
print('Valid IP - Status code:', resp2.status_code)
print('JSON:', resp2.get_json())
