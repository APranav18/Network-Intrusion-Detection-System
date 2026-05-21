import json
import importlib.util
from pathlib import Path

# Load the ip_detector module by path to avoid package import issues
module_path = Path('AI-Powered-Network-Intrusion-Detection-System') / 'utils' / 'ip_detector.py'
spec = importlib.util.spec_from_file_location('ip_detector', str(module_path))
ip_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ip_mod)

analyze = getattr(ip_mod, 'analyze_ip')

cases = [
    '185.220.101.42',  # known malicious reference
    '8.8.8.8',         # known benign reference
    '256.256.256.256', # invalid
]

for ip in cases:
    try:
        res = analyze(ip, use_cache=False)
    except Exception as e:
        res = {'error': str(e)}
    print(f"IP: {ip}\n{json.dumps(res, indent=2)}\n")

print('\n--- Direct model scores ---\n')
from importlib import reload
reload(ip_mod)
Model = getattr(ip_mod, 'RealtimeIPRiskModel')
model = Model()
for ip in cases:
    score = model.score(ip, {})
    print(f"IP: {ip} -> probability={score.get('probability')}, status={score.get('status')}, label={score.get('status_label')}")
