import requests
import json

token = "e6d66e746f363c4611467be0e68e426569ec9880"
video_id = "f26830d1f860ee5d64a367d584433f3b"

headers = {"Authorization": f"Token {token}"}
r = requests.get(f"https://rutube.ru/api/video/{video_id}/", headers=headers)
data = r.json()

print(json.dumps({
    "is_deleted": data.get("is_deleted"),
    "status": data.get("status"),
    "action_reason": data.get("action_reason"),
    "duration": data.get("duration")
}, indent=2, ensure_ascii=False))
