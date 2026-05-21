import os
import sys
import time
import subprocess

def start_server(cwd):
    # Start the Flask app in a subprocess
    proc = subprocess.Popen([sys.executable, 'run.py'], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc

def wait_for_server(url='http://127.0.0.1:5000/ip-detection/', timeout=15):
    import requests
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=1)
            if r.status_code in (200, 302):
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False

def run_playwright_test(url='http://127.0.0.1:5000/ip-detection/'):
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except Exception as e:
        print('Playwright not installed:', e)
        return 2

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until='domcontentloaded')

        # Fill invalid input (alphabetic/random) and submit
        page.fill('#ipInput', 'abcd123')
        page.click('#singleIPForm button[type=submit]')

        try:
            # Wait for the inline validation element to appear (not d-none)
            page.wait_for_selector('#ipValidationMsg:not(.d-none)', timeout=5000)
            text = page.inner_text('#ipValidationMsg')
            print('Validation message found:', text)
            browser.close()
            return 0 if 'invalid' in text.lower() or 'please enter' in text.lower() else 3
        except PWTimeout:
            print('Timeout: inline validation message did not appear')
            browser.close()
            return 4

def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    server = start_server(repo_root)
    try:
        ok = wait_for_server()
        if not ok:
            print('Server did not start within timeout')
            server.kill()
            return 5

        # Run the Playwright check
        rc = run_playwright_test()
        return rc
    finally:
        try:
            server.kill()
        except Exception:
            pass

if __name__ == '__main__':
    rc = main()
    sys.exit(rc)
