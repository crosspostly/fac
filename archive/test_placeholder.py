# -*- coding: utf-8 -*-
import requests
import json
import time

# --- НАСТРОЙКИ ---
LOGIN = 'nlpkem@ya.ru'
PASSWORD = '*V8u2p2r'
BASE_URL = "https://rutube.ru"

# Тестовое видео (Google Sample)
TEST_VIDEO_URL = "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"
TEST_TITLE = "Test Direct URL Upload (Placeholder)"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def run_test():
    # 1. Авторизация
    log("🔑 Авторизация...")
    try:
        r = requests.post(f"{BASE_URL}/api/accounts/token_auth/", data={'username': LOGIN, 'password': PASSWORD})
        if r.status_code != 200:
            log(f"❌ Ошибка авторизации: {r.text}")
            return
        token = r.json()['token']
        log(f"✅ Токен: {token[:10]}...")
    except Exception as e:
        log(f"❌ Ошибка сети: {e}")
        return

    # 2. Попытка создания черновика (без URL)
    log(f"📝 Попытка создания черновика (без URL)...")
    
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        # "url": TEST_VIDEO_URL,  <-- УБИРАЕМ URL
        "title": "Test Draft Mode",
        "description": "Trying to create empty container for file upload",
        "category_id": 13,
        "is_hidden": True
    }

    try:
        r_upload = requests.post(f"{BASE_URL}/api/video/", json=payload, headers=headers)
        
        if r_upload.status_code in [200, 201]:
            data = r_upload.json()
            video_id = data.get('video_id') or data.get('id')
            log(f"✅ УСПЕХ! Видео принято в очередь.")
            log(f"🆔 ID видео: {video_id}")
            
            # Проверка статуса (сразу)
            log("🔎 Проверяем статус...")
            time.sleep(2)
            r_status = requests.get(f"{BASE_URL}/api/video/{video_id}/", headers=headers)
            log(f"📄 Статус: {r_status.json().get('status')}")
            log(f"🗑 Удалено: {r_status.json().get('is_deleted')}")
            
        else:
            log(f"❌ Ошибка загрузки: {r_upload.status_code}")
            log(f"Ответ: {r_upload.text}")
            
    except Exception as e:
        log(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    run_test()
