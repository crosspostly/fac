# -*- coding: utf-8 -*-
import os
import requests
import json
import subprocess
import datetime
import time
import sqlite3
import threading
import sys
import config

# --- НАСТРОЙКИ ИЗ CONFIG.PY ---
LOGIN = config.RUTUBE_LOGIN
PASSWORD = config.RUTUBE_PASSWORD
YOUTUBE_CHANNEL_URL = config.YOUTUBE_CHANNEL_URL
BASE_URL = "https://rutube.ru"
DB_FILE = config.DB_FILE
BLACKLIST = ["ванга", "vanga", "прогноз", "знаков зодиака"]

# Local Server Settings
PUBLIC_IP = config.PUBLIC_IP
SERVER_PORT = config.SERVER_PORT
UPLOAD_FOLDER = config.UPLOADS_DIR

def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [MONITOR] {msg}")

def ensure_server_running():
    """Checks if local server is running, if not starts it."""
    try:
        r = requests.get(f"http://localhost:{SERVER_PORT}/health", timeout=2)
        if r.status_code == 200:
            # log("✅ Local server is running.")
            return True
    except:
        pass

    log("⚠️ Local server not running. Starting native server...")
    server_script = os.path.join(os.path.dirname(__file__), "server.py")
    
    # Start in background
    try:
        # Use subprocess.Popen to detach
        subprocess.Popen([sys.executable, server_script], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL,
                         start_new_session=True)
        time.sleep(2) # Wait for startup
        log("✅ Local server started.")
        return True
    except Exception as e:
        log(f"❌ Failed to start server: {e}")
        return False

def get_token():
    try:
        r = requests.post(f"{BASE_URL}/api/accounts/token_auth/", data={'username': LOGIN, 'password': PASSWORD}, timeout=30)
        return r.json().get('token') if r.status_code == 200 else None
    except: return None

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute('CREATE TABLE IF NOT EXISTS synced (y_id TEXT PRIMARY KEY, title TEXT)')
    conn.commit()
    conn.close()

def download_video_local(youtube_url, video_id):
    log(f"⬇️ Downloading video locally: {video_id}...")
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        
    try:
        output_template = f"{UPLOAD_FOLDER}/{video_id}.%(ext)s"
        # Try to find existing file first
        for f in os.listdir(UPLOAD_FOLDER):
            if f.startswith(video_id):
                log(f"✅ File already exists: {f}")
                return f

        cmd = [config.YT_DLP_PATH, "-f", "best[ext=mp4]/best", "-o", output_template, youtube_url]
        res = subprocess.run(cmd, capture_output=True, text=True)
        
        if res.returncode != 0:
            log(f"❌ Download failed: {res.stderr}")
            return None
            
        for f in os.listdir(UPLOAD_FOLDER):
            if f.startswith(video_id):
                log(f"✅ Download complete: {f}")
                return f
        return None
    except Exception as e:
        log(f"❌ Exception during download: {e}")
        return None

def sync_and_wait():
    init_db()
    ensure_server_running() # Ensure server is up
    
    token = get_token()
    if not token:
        log("❌ Ошибка авторизации")
        return

    log("🔎 Поиск видео на YouTube...")
    yt_dlp = config.YT_DLP_PATH
    
    # Add cookies if available
    cookies_arg = []
    if os.path.exists(config.YOUTUBE_COOKIES_FILE):
        cookies_arg = ["--cookies", config.YOUTUBE_COOKIES_FILE]

    cmd_list = [yt_dlp] + cookies_arg + ["--get-id", "--get-title", "--flat-playlist", "--playlist-end", "10", YOUTUBE_CHANNEL_URL]
    
    try:
        res = subprocess.run(cmd_list, capture_output=True, text=True)
        lines = res.stdout.strip().split("\n")
    except Exception as e:
        log(f"❌ Error listing videos: {e}")
        return
    
    selected = None
    for i in range(0, len(lines), 2):
        if i+1 >= len(lines): break
        title, y_id = lines[i], lines[i+1]
        
        conn = sqlite3.connect(DB_FILE)
        already_in = conn.execute('SELECT 1 FROM synced WHERE y_id=?', (y_id,)).fetchone()
        conn.close()
        
        if already_in or any(word in title.lower() for word in BLACKLIST):
            continue
            
        selected = {"title": title, "id": y_id}
        break

    if not selected:
        log("😴 Новых видео для загрузки нет.")
        return

    log(f"🎬 ВЫБРАНО: {selected['title']}")
    youtube_url = f"https://youtube.com/watch?v={selected['id']}"
    
    # STRATEGY 1: Direct Link (Fastest)
    upload_link = None
    log("🔗 Попытка 1: Прямая ссылка...")
    try:
        cmd_url = [yt_dlp] + cookies_arg + ["-g", "-f", "best[ext=mp4]/best", youtube_url]
        res_url = subprocess.run(cmd_url, capture_output=True, text=True)
        if res_url.returncode == 0 and res_url.stdout.strip():
            upload_link = res_url.stdout.strip()
            log("✅ Прямая ссылка получена.")
        else:
            log("⚠️ Не удалось получить прямую ссылку (возможно бот-чек).")
    except:
        pass

    # STRATEGY 2: Local Download + Server (Fallback)
    if not upload_link:
        log("🔄 Попытка 2: Скачивание + Локальный сервер...")
        filename = download_video_local(youtube_url, selected['id'])
        if filename:
            upload_link = f"http://{PUBLIC_IP}:{SERVER_PORT}/static/{filename}"
            log(f"✅ Локальная ссылка сформирована: {upload_link}")
        else:
            log("❌ Не удалось подготовить видео ни одним способом.")
            return


    # UPLOAD TO RUTUBE
    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
    payload = {
        "url": upload_link, 
        "title": selected['title'], 
        "category_id": 13, 
        "is_hidden": False,
        "description": f"Original: {youtube_url}"
    }
    
    log(f"🚀 Отправка в Rutube API...")
    r_rutube = requests.post(f"{BASE_URL}/api/video/", json=payload, headers=headers)
    if r_rutube.status_code not in [200, 201]:
        log(f"❌ API Ошибка: {r_rutube.text}")
        return

    video_id = r_rutube.json().get('video_id') or r_rutube.json().get('id')
    log(f"✅ Видео принято! ID: {video_id}. НАЧИНАЕМ МОНИТОРИНГ...")

    # MONITORING
    start_time = time.time()
    while time.time() - start_time < 1800: # 30 min max
        time.sleep(30)
        try:
            r = requests.get(f"{BASE_URL}/api/video/{video_id}/", headers=headers, timeout=20)
            if r.status_code != 200:
                continue
                
            data = r.json()
            status = data.get('status') # Usually null initially
            is_deleted = data.get('is_deleted')
            reason = data.get('action_reason', {}).get('name', 'none')
            
            # Rutube specific: is_deleted=True + action_reason='downloading_video' means it's working
            # Status becomes 'ready' when done.
            
            log(f"⏳ Статус: {status} | Reason: {reason} | Deleted: {is_deleted}")

            if status == 'ready':
                log("🎉🎉🎉 ВИДЕО ОПУБЛИКОВАНО!")
                conn = sqlite3.connect(DB_FILE)
                conn.execute('INSERT INTO synced VALUES (?, ?)', (selected['id'], selected['title']))
                conn.commit()
                conn.close()
                return
                
            if is_deleted and reason == 'no reason': # Deleted by moderation or error
                 # Wait a bit more to be sure it's not just initial state
                 if time.time() - start_time > 300: # If 5 mins passed and still deleted/no reason
                     log("❌ Видео удалено или ошибка загрузки.")
                     return

        except Exception as e:
            log(f"⚠️ Ошибка при мониторинге: {e}")

    log("⏰ Время ожидания истекло.")

if __name__ == "__main__":
    sync_and_wait()
