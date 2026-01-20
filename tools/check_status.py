import requests
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def check_status(video_id):
    r = requests.post("https://rutube.ru/api/accounts/token_auth/", data={'username': config.RUTUBE_LOGIN, 'password': config.RUTUBE_PASSWORD})
    if r.status_code != 200:
        print(f"Auth failed: {r.text}")
        return
    token = r.json().get('token')
    
    headers = {"Authorization": f"Token {token}"}
    print(f"🔍 Checking status for {video_id}...")
    
    r = requests.get(f"https://rutube.ru/api/video/{video_id}/", headers=headers)
    
    if r.status_code == 200:
        print(json.dumps(r.json(), indent=2, ensure_ascii=False))
    else:
        print(f"❌ Error {r.status_code}: {r.text}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 tools/check_status.py <video_id>")
    else:
        check_status(sys.argv[1])