import requests
import json

LOGIN = 'nlpkem@ya.ru'
PASSWORD = '*V8u2p2r'
IDS = [
    '6b327289541fee9509afc9c9cf5abed7',
    'a33a1aaf6c6f7a1c02a86e8e0c73f3e3',
    'f86dbb30b7965b0e973b260348edcc77'
]

def check_all():
    r = requests.post("https://rutube.ru/api/accounts/token_auth/", data={'username': LOGIN, 'password': PASSWORD})
    token = r.json().get('token')
    headers = {"Authorization": f"Token {token}"}
    
    print(f"{'ID':<34} | {'Status':<15} | {'Deleted':<8} | {'Reason'}")
    print("-" * 80)
    
    for vid in IDS:
        res = requests.get(f"https://rutube.ru/api/video/{vid}/", headers=headers)
        if res.status_code == 200:
            data = res.json()
            status = str(data.get('status'))
            deleted = str(data.get('is_deleted'))
            reason = data.get('action_reason', {}).get('name', 'N/A')
            print(f"{vid:<34} | {status:<15} | {deleted:<8} | {reason}")
        else:
            print(f"{vid:<34} | Error {res.status_code}")

if __name__ == "__main__":
    check_all()
