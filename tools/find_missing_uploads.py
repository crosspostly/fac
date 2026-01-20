import sqlite3
import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def get_rutube_titles():
    # ... (same auth logic)
    r = requests.post("https://rutube.ru/api/accounts/token_auth/", data={'username': config.RUTUBE_LOGIN, 'password': config.RUTUBE_PASSWORD})
    if r.status_code != 200: return []
    token = r.json().get('token')
    
    headers = {"Authorization": f"Token {token}"}
    r = requests.get("https://rutube.ru/api/profile/user/", headers=headers)
    if r.status_code != 200: 
        r = requests.get("https://rutube.ru/api/accounts/profile/", headers=headers)
        
    if r.status_code != 200: return []
    user_id = r.json().get('id')
    
    titles = set()
    # Fetch all pages
    url = f"https://rutube.ru/api/video/person/{user_id}/?limit=50"
    while url:
        r = requests.get(url, headers=headers)
        if r.status_code != 200: break
        data = r.json()
        for v in data.get('results', []):
            titles.add(v.get('title'))
        
        url = data.get('next') # Pagination
    return titles

def check_db():
    conn = sqlite3.connect(config.DB_FILE)
    cursor = conn.execute("SELECT y_id, title FROM synced")
    synced_videos = cursor.fetchall()
    conn.close()
    
    rutube_titles = get_rutube_titles()
    
    print(f"Found {len(rutube_titles)} videos on Rutube.")
    print(f"Found {len(synced_videos)} synced videos in DB.")
    
    missing = []
    for y_id, title in synced_videos:
        # Check if title exists in Rutube list
        # We use exact match because the bot uploads exact title.
        if title not in rutube_titles:
            missing.append((y_id, title))
            
    print("\n--- Videos marked as synced but NOT found on Rutube ---")
    for y_id, title in missing:
        print(f"❌ {title} (ID: {y_id})")
        
    if missing:
        print("\nTo fix this, run: python3 tools/clean_db.py")

if __name__ == "__main__":
    check_db()
