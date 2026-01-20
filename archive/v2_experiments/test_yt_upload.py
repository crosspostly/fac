# -*- coding: utf-8 -*-
import requests
import subprocess
import sys
import json
import time
import os

# --- НАСТРОЙКИ ---
LOGIN = 'nlpkem@ya.ru'
PASSWORD = '*V8u2p2r'
BASE_URL = "https://rutube.ru"
PUBLIC_IP = "34.79.212.248"
SERVER_PORT = "5005"
UPLOAD_FOLDER = "uploads"

def get_direct_url(youtube_url):
    print(f"🔗 Получение прямой ссылки с YouTube для {youtube_url}...")
    try:
        # Используем локальный yt-dlp
        cmd = ["./yt-dlp", "-g", "-f", "best[ext=mp4]/best", youtube_url]
        res = subprocess.run(cmd, capture_output=True, text=True)
        
        if res.returncode != 0:
            print(f"❌ Ошибка yt-dlp: {res.stderr}")
            return None
            
        direct_link = res.stdout.strip()
        if not direct_link:
            print("❌ yt-dlp вернул пустую строку")
            return None
            
        print(f"✅ Прямая ссылка получена")
        return direct_link
    except Exception as e:
        print(f"❌ Ошибка выполнения yt-dlp: {e}")
        return None

def download_video_local(youtube_url):
    print(f"⬇️ Скачивание видео локально для {youtube_url}...")
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        
    try:
        # Скачиваем в папку uploads с ID в качестве имени
        output_template = f"{UPLOAD_FOLDER}/%(id)s.%(ext)s"
        cmd = ["./yt-dlp", "-f", "best[ext=mp4]/best", "-o", output_template, youtube_url]
        res = subprocess.run(cmd, capture_output=True, text=True)
        
        if res.returncode != 0:
            print(f"❌ Ошибка скачивания yt-dlp: {res.stderr}")
            return None
            
        # Находим скачанный файл (мы не знаем точно расширение, но знаем ID)
        # Получим ID видео из URL или через yt-dlp --get-id, но проще распарсить output или поискать файл
        # Проще спросить ID у yt-dlp
        cmd_id = ["./yt-dlp", "--get-id", youtube_url]
        res_id = subprocess.run(cmd_id, capture_output=True, text=True)
        vid_id = res_id.stdout.strip()
        
        for f in os.listdir(UPLOAD_FOLDER):
            if f.startswith(vid_id):
                local_path = os.path.join(UPLOAD_FOLDER, f)
                print(f"✅ Видео скачано: {local_path}")
                return f # Возвращаем имя файла
        
        print("❌ Файл не найден после скачивания")
        return None

    except Exception as e:
        print(f"❌ Исключение при скачивании: {e}")
        return None

def auth():
    print(f"🔐 Авторизация ({LOGIN})...")
    try:
        r = requests.post(f"{BASE_URL}/api/accounts/token_auth/", data={'username': LOGIN, 'password': PASSWORD}, timeout=30)
        if r.status_code == 200:
            token = r.json().get('token')
            print("✅ Токен получен")
            return token
        else:
            print(f"❌ Ошибка авторизации: {r.text}")
            return None
    except Exception as e:
        print(f"❌ Ошибка сети при авторизации: {e}")
        return None

def upload_url(token, direct_url, title):
    print(f"🚀 Отправка задачи на загрузку: {title}...")
    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
    payload = {
        "url": direct_url,
        "title": title,
        "category_id": 13, # Хобби
        "is_hidden": True, # Скрытое, чтобы не мусорить
        "description": "Uploaded via API test script from YouTube URL"
    }
    
    try:
        r = requests.post(f"{BASE_URL}/api/video/", json=payload, headers=headers)
        if r.status_code in [200, 201]:
            video_id = r.json().get('video_id') or r.json().get('id')
            print(f"✅ Успешно! Video ID: {video_id}")
            return video_id
        else:
            print(f"❌ Ошибка API Rutube: {r.status_code} - {r.text}")
            return None
    except Exception as e:
        print(f"❌ Ошибка сети при загрузке: {e}")
        return None

def check_status(token, video_id):
    print(f"⏳ Проверка статуса видео {video_id}...")
    headers = {"Authorization": f"Token {token}"}
    
    for i in range(10): # Проверяем 10 раз
        try:
            r = requests.get(f"{BASE_URL}/api/video/{video_id}/", headers=headers)
            if r.status_code == 200:
                data = r.json()
                status = data.get('status')
                print(f"   [{i+1}] Статус: {status}")
                if status == 'ready':
                    print("🎉 Видео готово!")
                    return
                elif status == 'error':
                    print("❌ Ошибка обработки видео на стороне Rutube")
                    return
            else:
                print(f"   ⚠️ Не удалось получить статус: {r.status_code}")
        except Exception as e:
            print(f"   ⚠️ Ошибка: {e}")
        
        time.sleep(5)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python3 test_yt_upload.py <YOUTUBE_URL>")
        YOUTUBE_URL = "https://www.youtube.com/watch?v=aqz-KE-bpKQ" # Big Buck Bunny
        print(f"⚠️ Аргумент не передан, используем тестовое видео: {YOUTUBE_URL}")
    else:
        YOUTUBE_URL = sys.argv[1]

    # 2. Авторизуемся
    token = auth()
    if not token:
        sys.exit(1)

    # 3. Попытка 1: Прямая ссылка
    video_id = None
    
    # Если это уже прямая ссылка (на файл), то пробуем сразу
    if YOUTUBE_URL.lower().endswith(('.mp4', '.mkv', '.webm')):
        print(f"ℹ️ Обнаружена прямая ссылка, пропускаем yt-dlp.")
        video_id = upload_url(token, YOUTUBE_URL, "Test Upload Direct Link")
    else:
        # Пробуем получить ссылку через yt-dlp
        direct_link = get_direct_url(YOUTUBE_URL)
        if direct_link:
            print("Trying upload via Direct YouTube URL...")
            video_id = upload_url(token, direct_link, "Test Upload from YouTube API")
    
    # 4. Попытка 2: Скачивание + Статическая ссылка (Fallback)
    if not video_id:
        print("\n⚠️ Прямая загрузка не удалась. Включаем FALLBACK: Скачивание на сервер...")
        filename = download_video_local(YOUTUBE_URL)
        if filename:
            static_url = f"http://{PUBLIC_IP}:{SERVER_PORT}/static/{filename}"
            print(f"🔗 Сформирована статическая ссылка: {static_url}")
            
            # Проверка доступности (опционально)
            try:
                r_check = requests.head(static_url)
                print(f"   🔍 Проверка доступности файла: {r_check.status_code}")
            except:
                print("   ⚠️ Не удалось проверить доступность файла локально")

            video_id = upload_url(token, static_url, "Test Upload Fallback (Local Server)")

    # 5. Проверяем статус, если удалось отправить
    if video_id:
        check_status(token, video_id)
    else:
        print("🛑 Все методы загрузки не сработали.")

