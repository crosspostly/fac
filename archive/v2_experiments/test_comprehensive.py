# -*- coding: utf-8 -*-
import os
import requests
import subprocess
import sys
import time
import json
import datetime
import config

# --- CONFIGURATION ---
LOGIN = config.RUTUBE_LOGIN
PASSWORD = config.RUTUBE_PASSWORD
BASE_URL = "https://rutube.ru"
SERVER_PORT = config.SERVER_PORT
UPLOADS_DIR = config.UPLOADS_DIR
PUBLIC_DOMAIN = config.PUBLIC_IP
TEST_VIDEO_FILENAME = "test_video.mp4"
TEST_VIDEO_PATH = os.path.join(UPLOADS_DIR, TEST_VIDEO_FILENAME)
LOG_FILE_MD = "experiment_log.md"
LOG_FILE_JSON = "experiment_log.json"
SERVER_LOG = "server_debug.log"

# Strategies
STRATEGIES = [
    {
        "name": "REFERENCE_URL_HTTPS",
        "description": "Upload a stable public video from Google Storage (HTTPS)",
        "url": "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"
    },
    {
        "name": "LOCAL_WEBHOOK_PARAM",
        "description": "Serve local file via /webhook?file=... on public domain",
        "generate_url": lambda f: f"https://{PUBLIC_DOMAIN}/rutube-webhook/webhook?file={f}"
    },
    {
        "name": "LOCAL_STATIC_PATH",
        "description": "Serve local file via /static/... on public domain",
        "generate_url": lambda f: f"https://{PUBLIC_DOMAIN}/rutube-webhook/static/{f}"
    },
    {
        "name": "EXTERNAL_FILE_IO",
        "description": "Upload file to file.io and use that link",
        "action": "upload_file_io"
    }
]

class RutubeTester:
    def __init__(self):
        self.token = None
        self.ensure_server()
        self.authenticate()

    def log(self, msg):
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

    def ensure_server(self):
        try:
            requests.get(f"http://localhost:{SERVER_PORT}/health", timeout=1)
            self.log("✅ Local server is running.")
        except:
            self.log("⚠️ Local server not running. Starting with logging...")
            server_script = os.path.join(os.path.dirname(__file__), "server_simple.py")
            # Open log file
            self.server_log_file = open(SERVER_LOG, "w")
            self.server_process = subprocess.Popen(
                [sys.executable, server_script],
                stdout=self.server_log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
            time.sleep(3)
            self.log(f"✅ Local server started. Logs at {SERVER_LOG}")

    def authenticate(self):
        self.log("Authenticating...")
        try:
            r = requests.post(f"{BASE_URL}/api/accounts/token_auth/", data={'username': LOGIN, 'password': PASSWORD})
            if r.status_code == 200:
                self.token = r.json().get('token')
                self.log(f"✅ Authenticated. Token: {self.token[:10]}...")
            else:
                self.log(f"❌ Auth failed: {r.text}")
                sys.exit(1)
        except Exception as e:
            self.log(f"❌ Auth exception: {e}")
            sys.exit(1)

    def upload_to_file_io(self, file_path):
        self.log("Uploading to file.io...")
        try:
            # file.io expires after 1 download usually, but 'expires' param can extend?
            # Default is 14 days, auto delete on download = true.
            # Rutube needs to download it once.
            cmd = ["curl", "-F", f"file=@{file_path}", "https://file.io"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                try:
                    data = json.loads(res.stdout)
                    if data.get('success'):
                        url = data.get('link')
                        self.log(f"✅ Uploaded to file.io: {url}")
                        return url
                except: pass
                self.log(f"❌ file.io response parse error: {res.stdout}")
                return None
            else:
                self.log(f"❌ file.io failed: {res.stderr}")
                return None
        except Exception as e:
            self.log(f"❌ file.io exception: {e}")
            return None

    def run_strategy(self, strategy):
        name = strategy['name']
        desc = strategy['description']
        self.log(f"\n🚀 STARTING STRATEGY: {name}")
        self.log(f"ℹ️ {desc}")

        # Determine URL
        video_url = None
        if 'url' in strategy:
            video_url = strategy['url']
        elif 'generate_url' in strategy:
            video_url = strategy['generate_url'](TEST_VIDEO_FILENAME)
        elif 'action' in strategy and strategy['action'] == 'upload_file_io':
            video_url = self.upload_to_file_io(TEST_VIDEO_PATH)

        if not video_url:
            self.log("❌ Failed to determine video URL. Skipping.")
            self.record_result(name, "N/A", "Failed to generate URL", "ERROR")
            return

        self.log(f"🔗 Video URL: {video_url}")

        # Upload to Rutube
        title = f"[TEST-{name}] {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        headers = {"Authorization": f"Token {self.token}", "Content-Type": "application/json"}
        payload = {
            "url": video_url,
            "title": title,
            "category_id": 13,
            "is_hidden": True,
            "description": f"Test upload strategy: {name}"
        }

        try:
            r = requests.post(f"{BASE_URL}/api/video/", json=payload, headers=headers)
            
            if r.status_code not in [200, 201]:
                self.log(f"❌ API Request Failed: {r.text}")
                self.record_result(name, video_url, r.text, "API_ERROR")
                return

            data = r.json()
            video_id = data.get('video_id') or data.get('id')
            self.log(f"✅ Request Accepted. Video ID: {video_id}")

            # Poll for result
            final_status = self.poll_status(video_id, headers)
            self.record_result(name, video_url, json.dumps(final_status), final_status.get('status_code', 'UNKNOWN'))
            
            # If local strategy, check logs
            if "LOCAL" in name:
                self.check_server_log()

        except Exception as e:
            self.log(f"❌ Exception during upload: {e}")
            self.record_result(name, video_url, str(e), "EXCEPTION")

    def poll_status(self, video_id, headers):
        # Increased polling for testing (3 mins) 
        max_retries = 36 
        self.log("⏳ Polling for status...")
        
        for i in range(max_retries):
            time.sleep(5)
            try:
                r = requests.get(f"{BASE_URL}/api/video/{video_id}/", headers=headers)
                if r.status_code == 200:
                    data = r.json()
                    is_deleted = data.get('is_deleted', False)
                    
                    if is_deleted:
                        reason = data.get('action_reason', {}).get('name', 'Unknown')
                        self.log(f"❌ Video DELETED by Rutube. Reason: {reason}")
                        return {"status_code": "DELETED", "data": data, "reason": reason}

                    if i % 6 == 0:
                        self.log(f"Checking... (Attempt {i+1}/{max_retries}) - Alive.")

                else:
                    self.log(f"⚠️ Status check HTTP {r.status_code}")
            except Exception as e:
                self.log(f"⚠️ Polling exception: {e}")

        self.log("✅ Timeout reached (Video survived 3 mins). Marking as TENTATIVE_SUCCESS.")
        return {"status_code": "TENTATIVE_SUCCESS", "note": "Survived polling duration"}

    def check_server_log(self):
        self.log("🔎 Checking server logs for hits...")
        if os.path.exists(SERVER_LOG):
            with open(SERVER_LOG, 'r') as f:
                lines = f.readlines()
                # Show last 5 lines
                for line in lines[-5:]:
                    print(f"    LOG: {line.strip()}")
        else:
            self.log("⚠️ No server log file found.")

    def record_result(self, method, url, details, status):
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "method": method,
            "url": url,
            "status": status,
            "details_snippet": str(details)[:200]
        }
        
        # JSON
        try:
            existing = []
            if os.path.exists(LOG_FILE_JSON):
                with open(LOG_FILE_JSON, 'r') as f:
                    try:
                        existing = json.load(f)
                    except: pass
            existing.append(entry)
            with open(LOG_FILE_JSON, 'w') as f:
                json.dump(existing, f, indent=2)
        except Exception as e:
            self.log(f"Error writing JSON log: {e}")

        # MD
        md_line = f"| {entry['timestamp']} | **{method}** | `{status}` | [Link]({url}) | {entry['details_snippet']} |\n"
        
        if not os.path.exists(LOG_FILE_MD):
            with open(LOG_FILE_MD, 'w') as f:
                f.write("# Rutube Upload Experiments\n\n| Time | Method | Status | URL | Details |\n|---|---|---|---|---|\n")
        
        with open(LOG_FILE_MD, 'a') as f:
            f.write(md_line)

        self.log("📝 Result recorded.")

if __name__ == "__main__":
    tester = RutubeTester()
    
    # Run all strategies
    for strategy in STRATEGIES:
        tester.run_strategy(strategy)
        time.sleep(5) # Cooldown