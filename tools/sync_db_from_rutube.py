import sqlite3
import requests
import subprocess
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def get_rutube_videos():
    print("🌍 Fetching Rutube videos...")
    r = requests.post("https://rutube.ru/api/accounts/token_auth/", data={'username': config.RUTUBE_LOGIN, 'password': config.RUTUBE_PASSWORD})
    if r.status_code != 200: 
        print("❌ Auth failed")
        return []
    token = r.json().get('token')
    
    headers = {"Authorization": f"Token {token}"}
    r = requests.get("https://rutube.ru/api/profile/user/", headers=headers)
    if r.status_code != 200: 
        r = requests.get("https://rutube.ru/api/accounts/profile/", headers=headers)
    
    if r.status_code != 200: return []
    user_id = r.json().get('id')
    
    videos = []
    url = f"https://rutube.ru/api/video/person/{user_id}/?limit=50"
    while url:
        r = requests.get(url, headers=headers)
        if r.status_code != 200: break
        data = r.json()
        for v in data.get('results', []):
            videos.append(v)
        url = data.get('next')
    print(f"✅ Found {len(videos)} videos on Rutube.")
    return videos

def get_youtube_videos():
    print("🌍 Fetching YouTube videos...")
    cmd = [config.YT_DLP_PATH, "--dump-json", "--flat-playlist", "--playlist-end", "50", config.YOUTUBE_CHANNEL_URL]
    res = subprocess.run(cmd, capture_output=True, text=True)
    videos = []
    for line in res.stdout.strip().split("\n"):
        if line: videos.append(json.loads(line))
    print(f"✅ Found {len(videos)} videos on YouTube (last 50).")
    return videos

def sync_db():
    rutube_vids = get_rutube_videos()
    youtube_vids = get_youtube_videos()
    
    # Create map Title -> Rutube Video
    # Note: Titles must match exactly.
    rutube_map = {v.get('title'): v for v in rutube_vids}
    
    conn = sqlite3.connect(config.DB_FILE)
    conn.execute('CREATE TABLE IF NOT EXISTS synced (y_id TEXT PRIMARY KEY, title TEXT)')
    
    added_count = 0
    for yt_vid in youtube_vids:
        title = yt_vid.get('title')
        y_id = yt_vid.get('id')
        
        # Check if already synced in DB
        cursor = conn.execute('SELECT 1 FROM synced WHERE y_id=?', (y_id,))
        if cursor.fetchone():
            continue
            
        # Check if exists on Rutube
        if title in rutube_map:
            print(f"🔗 Match found! Marking as synced: {title}")
            conn.execute('INSERT OR REPLACE INTO synced VALUES (?, ?)', (y_id, title))
            added_count += 1
            
    conn.commit()
    conn.close()
    print(f"🎉 Synced {added_count} videos from Rutube to local DB.")

if __name__ == "__main__":
    sync_db()
