# -*- coding: utf-8 -*-
import requests
import json
import os
import datetime

# --- ДАННЫЕ ---
VIDEO_FILE = "rutube/test_video.mp4" 
BASE_URL = "https://rutube.ru"

def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

def run():
    # 1. Получаем токен по логину/паролю
    login = 'nlpkem@ya.ru'
    password = '*V8u2p2r'
    log(f"🔄 Авторизация {login}...")
    
    try:
        r_auth = requests.post(f"{BASE_URL}/api/accounts/token_auth/", data={'username': login, 'password': password})
        if r_auth.status_code != 200:
            log(f"❌ Ошибка авторизации: {r_auth.text}")
            return
        
        token = r_auth.json()['token']
        log(f"✅ Токен получен: {token[:10]}...")

        # Заголовки с Токеном (API Token не требует Bearer, обычно просто Token)
        headers = {
            "Authorization": f"Token {token}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        log("🚀 Шаг 1: Создание черновика (Create)...")
        create_url = f"{BASE_URL}/api/video/create/"
        payload = {
            "title": f"API File Upload {datetime.datetime.now().strftime('%H:%M')}",
            "description": "Uploaded via Python Requests (Token)",
            "category_id": 13,
            "is_hidden": False
        }

        r_create = requests.post(create_url, json=payload, headers=headers)
        log(f"Статус Create: {r_create.status_code}")
        
        if r_create.status_code not in [200, 201]:
            log(f"❌ Ошибка создания: {r_create.text}")
            # Если 403, значит этот токен не имеет прав на создание видео файлом
            return

        data = r_create.json()
        video_id = data.get('video_id') or data.get('id')
        log(f"✅ Черновик создан! Video ID: {video_id}")

        # --- ШАГ 2: Загрузка файла ---
        log(f"🚀 Шаг 2: Загрузка файла (Upload)...")
        upload_url = f"{BASE_URL}/api/video/upload/{video_id}/"
        
        if not os.path.exists(VIDEO_FILE):
            log(f"❌ Файл {VIDEO_FILE} не найден!")
            return

        files = {
            'video_file': ('test.mp4', open(VIDEO_FILE, 'rb'), 'video/mp4')
        }
        
        form_data = {
            'video_id': video_id,
            'title': payload['title']
        }

        r_upload = requests.post(upload_url, headers=headers, files=files, data=form_data)
        
        log(f"Статус Upload: {r_upload.status_code}")
        log(f"Ответ сервера: {r_upload.text}")

        if r_upload.status_code in [200, 201, 202]:
            log("🎉 УСПЕХ! Видео отправлено в обработку.")
        else:
            log("❌ Загрузка файла провалилась.")

    except Exception as e:
        log(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    run()