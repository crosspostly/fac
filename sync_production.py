# -*- coding: utf-8 -*-
import os
import requests
import subprocess
import time
import datetime
import json
import sqlite3
import config

# Import social uploader
try:
    from social_uploader import process_social_uploads, get_video_orientation
except ImportError:
    print("⚠️ Social uploader module not found.")
    process_social_uploads = None
    get_video_orientation = lambda x: 'horizontal' # Fallback

# Lazy import placeholder
set_cover_frame = None

# Try importing Playwright module safely
try:
    from set_frame_playwright import set_cover_frame
except ImportError:
    print("⚠️ Playwright module not found. Cover frame will not be set.")

# --- НАСТРОЙКИ ---
LOGIN = config.RUTUBE_LOGIN
PASSWORD = config.RUTUBE_PASSWORD
PUBLIC_DOMAIN = config.PUBLIC_IP
PORT = config.SERVER_PORT
YOUTUBE_CHANNEL_URL = config.YOUTUBE_CHANNEL_URL
YT_DLP_PATH = config.YT_DLP_PATH
UPLOADS_DIR = config.UPLOADS_DIR
DB_FILE = config.DB_FILE

def log(msg):
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute('CREATE TABLE IF NOT EXISTS synced (y_id TEXT PRIMARY KEY, title TEXT)')
    conn.commit()
    conn.close()

def is_video_synced(y_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.execute('SELECT 1 FROM synced WHERE y_id=?', (y_id,))
    exists = cursor.fetchone()
    conn.close()
    return exists is not None

def mark_video_synced(y_id, title):
    conn = sqlite3.connect(DB_FILE)
    conn.execute('INSERT OR REPLACE INTO synced VALUES (?, ?)', (y_id, title))
    conn.commit()
    conn.close()

def get_auth_token():
    r = requests.post("https://rutube.ru/api/accounts/token_auth/", data={'username': LOGIN, 'password': PASSWORD})
    return r.json().get('token') if r.status_code == 200 else None

def wait_for_processing(video_id, token, max_retries=120, delay=5):
    headers = {"Authorization": f"Token {token}"}
    for i in range(max_retries):
        try:
            r = requests.get(f"https://rutube.ru/api/video/{video_id}/", headers=headers)
            if r.status_code == 200:
                data = r.json()
                status = data.get('status')
                action_reason = data.get('action_reason', {}).get('name')
                is_deleted = data.get('is_deleted')

                if status == 'ready' or action_reason == 'moderation':
                    return True
                
                if status == 'error' or (is_deleted and action_reason != 'downloading_video'):
                    log(f"❌ Видео перешло в статус {status} или удалено (reason: {action_reason})")
                    return False
            else:
                log(f"⚠️ Ошибка проверки статуса: {r.status_code}")
        except Exception as e:
            log(f"⚠️ Ошибка сети при проверке статуса: {e}")
        
        time.sleep(delay)
    
    log("⏰ Превышено время ожидания обработки видео")
    return False

def get_full_video_info(y_id):
    """Fetches full video metadata including full description."""
    try:
        cmd = [YT_DLP_PATH, "--dump-json"]
        if os.path.exists("youtube_cookies.txt"):
             cmd.extend(["--cookies", "youtube_cookies.txt"])
        cmd.append(f"https://youtube.com/watch?v={y_id}")
        
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            return json.loads(res.stdout)
    except Exception as e:
        log(f"⚠️ Ошибка получения полной информации о видео: {e}")
    return None

def process_video(y_id, title, description, token):
    log(f"🚀 Обработка: {title}")
    local_file_base = os.path.join(UPLOADS_DIR, y_id)
    local_video_path = f"{local_file_base}.mp4"
    local_thumb_path = f"{local_file_base}.jpg"
    
    # Скачивание (только видео)
    if not os.path.exists(local_video_path):
        # Add cookies if available
        yt_cmd = [YT_DLP_PATH, "-f", "best[ext=mp4]", "-o", f"{local_file_base}.%(ext)s"]
        if os.path.exists("youtube_cookies.txt"):
             yt_cmd.extend(["--cookies", "youtube_cookies.txt"])
        yt_cmd.append(f"https://youtube.com/watch?v={y_id}")
        
        subprocess.run(yt_cmd)

    if not os.path.exists(local_video_path):
        log(f"❌ Ошибка: Файл не скачался (YouTube block?). Пропускаем загрузку.")
        return False

    # --- EXTERNAL UPLOAD (Catbox) ---
    def upload_to_catbox(path):
        log(f"📦 Uploading to Catbox (External Host)...")
        try:
            files = {'reqtype': (None, 'fileupload'), 'fileToUpload': open(path, 'rb')}
            resp = requests.post("https://catbox.moe/user/api.php", files=files)
            if resp.status_code == 200:
                return resp.text.strip()
            log(f"❌ Catbox Error: {resp.text}")
        except Exception as e:
            log(f"❌ Catbox Exception: {e}")
        return None

    # Try external upload first
    video_url = upload_to_catbox(local_video_path)
    
    # Fallback to local server if external fails (or if file too big)
    if not video_url:
        log("⚠️ External upload failed. Falling back to Local Server URL.")
        video_url = f"https://{PUBLIC_DOMAIN}/rutube-webhook/static/{y_id}.mp4"
    else:
        log(f"✅ External URL: {video_url}")
    # --------------------------------

    headers = {"Authorization": f"Token {token}"}
    payload = {
        "url": video_url,
        "title": title,
        "is_hidden": False,
        "category_id": 13,
        "description": description
    }

    r = requests.post("https://rutube.ru/api/video/", json=payload, headers=headers)
    if r.status_code in [200, 201]:
        data = r.json()
        rutube_video_id = data.get('id') or data.get('video_id')
        
        if not rutube_video_id:
            log(f"❌ ID видео не найден в ответе! Статус: {r.status_code}")
            log(f"📄 Полный ответ API: {r.text}")
            return False
            
        log(f"✅ Успешно отправлено! ID: {rutube_video_id}")
        
        # Ждем обработки
        if wait_for_processing(rutube_video_id, token):
            log("✅ Видео обработано.")
            
            # Устанавливаем кадр обложки (SAFE MODE)
            if set_cover_frame:
                try:
                    log(f"🖼️ Установка кадра 00:01 для видео {rutube_video_id}...")
                    set_cover_frame(rutube_video_id, title)
                except Exception as e:
                    log(f"⚠️ Ошибка установки кадра (Playwright): {e}")
            else:
                log("ℹ️ Пропуск установки кадра (Playwright не загружен).")
        else:
            log("⚠️ Ошибка обработки видео")

        # --- SOCIAL MEDIA UPLOAD ---
        # Вызываем загрузчик для соцсетей (TikTok/Insta)
        # Внутри process_social_uploads будет проверка ориентации!
        if process_social_uploads:
            try:
                # Use the path we just downloaded
                process_social_uploads(local_video_path, title, description)
            except Exception as e:
                log(f"⚠️ Ошибка загрузки в соцсети: {e}")
        # ---------------------------

        # Cleanup local file to save space
        if os.path.exists(local_video_path):
            try:
                os.remove(local_video_path)
                log(f"🗑️ Удален локальный файл: {local_video_path}")
            except Exception as e:
                log(f"⚠️ Ошибка удаления файла: {e}")

        mark_video_synced(y_id, title)
        return True
    log(f"❌ Ошибка API: {r.text}")
    return False

def sync():
    init_db()
    token = get_auth_token()
    if not token: 
        log("❌ Не удалось получить токен API")
        return

    # Простая проверка последних видео
    cmd = [YT_DLP_PATH, "--dump-json", "--flat-playlist", "--playlist-end", "5"]
    if os.path.exists("youtube_cookies.txt"):
         cmd.extend(["--cookies", "youtube_cookies.txt"])
    cmd.append(YOUTUBE_CHANNEL_URL)
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    
    videos = []
    for line in res.stdout.strip().split("\n"):
        if line: videos.append(json.loads(line))
    
    # 1. Проверяем top-5
    for vid in videos:
        y_id = vid.get('id')
        if not is_video_synced(y_id):
            # Fetch full details to get complete description
            full_info = get_full_video_info(y_id)
            if full_info:
                title = full_info.get('title', vid.get('title'))
                description = full_info.get('description', vid.get('description', ''))
                process_video(y_id, title, description, token)
            else:
                log(f"⚠️ Не удалось получить полную информацию для {y_id}, используем частичную.")
                process_video(y_id, vid.get('title'), vid.get('description', ''), token)
            return

    # Если мы здесь, значит все top-5 уже синхронизированы.
    if not videos:
        log("⚠️ Не найдено видео на канале.")
        return

    # 2. Проверяем дату самого свежего видео
    most_recent_date = None
    for vid in videos:
        d_str = vid.get('upload_date')
        if d_str:
            try:
                d = datetime.datetime.strptime(d_str, "%Y%m%d")
                if most_recent_date is None or d > most_recent_date:
                    most_recent_date = d
            except ValueError:
                pass
    
    should_expand = False
    if most_recent_date:
        days_diff = (datetime.datetime.now() - most_recent_date).days
        if days_diff > 7:
            should_expand = True
            log(f"🕵️ Последнее видео было {days_diff} дн. назад. Расширяем поиск до 50...")
    else:
        should_expand = True
    
    if should_expand:
        # 3. Расширенный поиск (50 видео)
        cmd_expanded = [YT_DLP_PATH, "--dump-json", "--flat-playlist", "--playlist-end", "50", YOUTUBE_CHANNEL_URL]
        res_expanded = subprocess.run(cmd_expanded, capture_output=True, text=True)
        
        expanded_videos = []
        for line in res_expanded.stdout.strip().split("\n"):
            if line: expanded_videos.append(json.loads(line))
        
        for vid in expanded_videos:
            y_id = vid.get('id')
            if not is_video_synced(y_id):
                log(f"🕰️ Найдено старое несинхронизированное видео: {vid.get('title')}")
                
                # Fetch full details
                full_info = get_full_video_info(y_id)
                if full_info:
                    title = full_info.get('title', vid.get('title'))
                    description = full_info.get('description', vid.get('description', ''))
                    process_video(y_id, title, description, token)
                else:
                    process_video(y_id, vid.get('title'), vid.get('description', ''), token)
                return
        
        log("✅ Все видео (из последних 50) уже синхронизированы.")
    else:
        log("✅ Все последние видео (5) синхронизированы и канал активен.")

if __name__ == "__main__":
    sync()