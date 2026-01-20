import requests
import json

LOGIN = 'nlpkem@ya.ru'
PASSWORD = '*V8u2p2r'
VIDEO_ID = '157f34393eee46cdaefb80740718ca70'

def check():
    print("Auth...")
    r = requests.post("https://rutube.ru/api/accounts/token_auth/", data={'username': LOGIN, 'password': PASSWORD})
    token = r.json()['token']
    
    print(f"Checking {VIDEO_ID}...")
    r_vid = requests.get(f"https://rutube.ru/api/video/{VIDEO_ID}/", headers={"Authorization": f"Token {token}"})
    print(json.dumps(r_vid.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    check()