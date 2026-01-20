import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def get_auth_token():
    r = requests.post("https://rutube.ru/api/accounts/token_auth/", data={'username': config.RUTUBE_LOGIN, 'password': config.RUTUBE_PASSWORD})
    if r.status_code == 200:
        return r.json().get('token')
    print(f"Auth failed: {r.text}")
    return None

def list_rutube_videos():
    token = get_auth_token()
    if not token: return

    headers = {"Authorization": f"Token {token}"}
    # Get list of my videos
    # Endpoint might be /api/video/person/ or similar. 
    # Usually /api/video/ returns public videos, but for "my" videos we need authenticated context.
    # Trying /api/video/person/ (undocumented but common) or just checking via search?
    # Better: /api/video/person/<user_id> but we don't know user_id easily.
    # Let's try /api/info/current_user/ first to get ID.
    
    r = requests.get("https://rutube.ru/api/profile/user/", headers=headers)
    if r.status_code != 200:
        # Try another one
        r = requests.get("https://rutube.ru/api/accounts/profile/", headers=headers)

    if r.status_code != 200:
        print(f"Failed to get user info. Status: {r.status_code}")
        print(f"Response: {r.text[:500]}")
        return

    try:
        user_id = r.json().get('id')
    except:
         print(f"JSON Error. Response: {r.text[:500]}")
         return
         
    print(f"User ID: {user_id}")
    
    url = f"https://rutube.ru/api/video/person/{user_id}/?limit=20"
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(f"Failed to list videos: {r.status_code} {r.text}")
        return

    data = r.json()
    results = data.get('results', [])
    print(f"Found {len(results)} videos on Rutube channel:")
    for v in results:
        print(f"- [{v.get('status')}] {v.get('title')} (ID: {v.get('id')}) - Hidden: {v.get('is_hidden')}")

if __name__ == "__main__":
    list_rutube_videos()