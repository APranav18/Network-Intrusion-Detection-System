import requests
import re
import sys

s = requests.Session()
base = 'http://127.0.0.1:5000'

try:
    r = s.get(base + '/auth/login', timeout=10)
except Exception as e:
    print(f'Error connecting to {base}: {e}')
    sys.exit(1)

if r.status_code != 200:
    print('Failed to fetch login page', r.status_code)
    sys.exit(1)

m = re.search(r'name="csrf_token"\s+type="hidden"\s+value="([^"]+)"', r.text)
if not m:
    m = re.search(r'value="([^"]+)"\s+name="csrf_token"', r.text)
if not m:
    print('CSRF token not found; proceeding without token')
    token = ''
else:
    token = m.group(1)

login_data = {
    'username': 'admin',
    'password': 'admin123',
    'remember_me': 'y'
}
if token:
    login_data['csrf_token'] = token

r = s.post(base + '/auth/login', data=login_data, allow_redirects=True, timeout=10)
print('Login status:', r.status_code, '->', r.url)

if r.status_code != 200 and r.status_code != 302:
    print('Login may have failed; response length:', len(r.text))

tests = ['999.999.999.999', '8.8.8.8', '185.220.101.42']
for ip in tests:
    try:
        resp = s.post(base + '/ip-detection/analyze', json={'ip': ip, 'use_cache': False}, timeout=20)
        print('\n=== Test IP:', ip, 'Status:', resp.status_code, '===')
        try:
            print(resp.json())
        except Exception as e:
            print('Non-JSON response:', resp.text[:1000])
    except Exception as e:
        print(f'\n=== Test IP: {ip} Error: {e} ===')
