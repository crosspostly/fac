import sqlite3
import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def get_rutube_titles():
    # ... (Duplicate logic, simplified for brevity or reuse)
    # Ideally import from find_missing_uploads but it's a script. 
    # Copy-paste for safety to be self-contained.
    
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
    url = f"https://rutube.ru/api/video/person/{user_id}/?limit=50"
    while url:
        r = requests.get(url, headers=headers)
        if r.status_code != 200: break
        data = r.json()
        for v in data.get('results', []):
            titles.add(v.get('title'))
        url = data.get('next')
    return titles

def clean_db():
    print("Fetching Rutube videos...")
    rutube_titles = get_rutube_titles()
    
    conn = sqlite3.connect(config.DB_FILE)
    cursor = conn.execute("SELECT y_id, title FROM synced")
    synced_videos = cursor.fetchall()
    
    removed_count = 0
    for y_id, title in synced_videos:
        if title not in rutube_titles:
            print(f"🗑️ Removing from DB: {title} (ID: {y_id})")
            conn.execute("DELETE FROM synced WHERE y_id=?", (y_id,))
            removed_count += 1
            
    conn.commit()
    conn.close()
    print(f"✅ Removed {removed_count} entries. Run the sync script now to re-upload them.")

if __name__ == "__main__":
    clean_db()