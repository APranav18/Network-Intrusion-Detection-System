import requests
import re
import sys

s = requests.Session()
base = 'http://127.0.0.1:5000'

# Get CSRF token from login page
r = s.get(base + '/auth/login')
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

login_data = {'username': 'admin', 'password': 'admin123', 'remember_me': 'y'}
if token:
    login_data['csrf_token'] = token

r = s.post(base + '/auth/login', data=login_data, allow_redirects=True)
print('Login status:', r.status_code, '->', r.url)

if r.status_code not in (200, 302):
    print('Login may have failed; aborting')
    sys.exit(1)

ip_to_capture = '8.8.8.8'
resp = s.post(base + '/ip-detection/start-capture', json={'ip': ip_to_capture, 'interface': None, 'timeout': 60})
print('Start capture response status:', resp.status_code)
try:
    print(resp.json())
except Exception:
    print(resp.text)

# Query live-status
resp2 = s.get(base + '/ip-detection/live-status')
print('\nLive status:', resp2.status_code)
try:
    print(resp2.json())
except Exception:
    print(resp2.text)

# If capture started, stop it after short delay
if resp.status_code == 200:
    print('\nStopping capture...')
    rstop = s.post(base + '/ip-detection/stop-capture', json={})
    print('Stop response:', rstop.status_code)
    try:
        print(rstop.json())
    except Exception:
        print(rstop.text)
