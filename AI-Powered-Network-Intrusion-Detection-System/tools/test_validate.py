import sys
import os

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.helpers import validate_ip
from utils.ip_detector import IPValidator

tests = ['not-an-ip','256.256.256.256','8.8.8.8','2001:4860:4860::8888','1234::abcd::1']
for t in tests:
    print(f"{t} helpers.validate_ip -> {validate_ip(t)} | IPValidator.is_valid_ip -> {IPValidator.is_valid_ip(t)}")

print('\nTesting IPAnalyzer.analyze responses:')
from utils.ip_detector import IPAnalyzer
an = IPAnalyzer()
for t in ['not-an-ip', '8.8.8.8']:
    res = an.analyze(t)
    print(t, '->', res.get('success'), res.get('error'))
