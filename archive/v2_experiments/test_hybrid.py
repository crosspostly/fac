# -*- coding: utf-8 -*-
import requests
import time
import subprocess
import sys
import config

LOGIN = config.RUTUBE_LOGIN
PASSWORD = config.RUTUBE_PASSWORD
BASE_URL = "https://rutube.ru"

# Google Storage Reference (Proven to work for private uploads)
VIDEO_URL = "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"

def run_hybrid_test():
    print("🚀 Starting HYBRID Test: API Private Upload -> Playwright Public Switch")
    
    # 1. Auth
    print("🔑 Authenticating...")
    r = requests.post(f"{BASE_URL}/api/accounts/token_auth/", data={'username': LOGIN, 'password': PASSWORD})
    token = r.json().get('token')
    if not token:
        print("❌ Auth failed")
        return

    # 2. Upload Private
    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
    payload = {
        "url": VIDEO_URL,
        "title": "[HYBRID-TEST] API+Playwright",
        "description": "Uploaded private via API, made public via Playwright",
        "category_id": 13,
        "is_hidden": True # PRIVATE
    }
    
    print("📤 Uploading via API (Hidden)...")
    r_up = requests.post(f"{BASE_URL}/api/video/", json=payload, headers=headers)
    if r_up.status_code not in [200, 201]:
        print(f"❌ API Upload failed: {r_up.text}")
        return

    video_id = r_up.json().get('video_id') or r_up.json().get('id')
    print(f"✅ Upload accepted. ID: {video_id}")
    
    # 3. Wait for processing (Rutube needs to fetch it first)
    print("⏳ Waiting for processing (max 2 mins)...")
    ready = False
    for i in range(24):
        time.sleep(5)
        r_st = requests.get(f"{BASE_URL}/api/video/{video_id}/", headers=headers)
        if r_st.status_code == 200:
            data = r_st.json()
            if data.get('is_deleted'):
                print(f"❌ Video deleted by Rutube: {data.get('action_reason')}")
                return
            
            # If it has duration, it's processed enough to be edited?
            # Or if it's just 'status' == 'ready'? 
            # We'll try to edit it as soon as it's not deleted and exists for a bit.
            if i > 2: # Wait at least 15s
                print("✅ Video seems stable. Attempting to publish...")
                ready = True
                break
        else:
            print(f"⚠️ Status check error: {r_st.status_code}")
    
    if not ready:
        print("❌ Timeout waiting for video stability.")
        return

    # 4. Call Playwright Publisher
    print("🤖 Calling Playwright Publisher...")
    cmd = [sys.executable, "rutube_publisher.py", str(video_id)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    
    print("--- Playwright Output ---")
    print(res.stdout)
    print("--- Playwright Errors ---")
    print(res.stderr)
    
    if res.returncode == 0:
        print("🎉 Hybrid Workflow Finished.")
    else:
        print("❌ Playwright script failed.")

if __name__ == "__main__":
    run_hybrid_test()
