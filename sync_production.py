# -*- coding: utf-8 -*-
import os
import sys
import requests
import subprocess
import time
import datetime
import json
import sqlite3
import shutil
import config
import atexit

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
UPLOADS_DIR = config.UPLOADS_DIR
DB_FILE = config.DB_FILE

# Metadata cache file for quick lookups
METADATA_CACHE_FILE = "video_metadata_cache.json"

# Resolve yt-dlp path
YT_DLP_PATH = config.YT_DLP_PATH
if not os.path.exists(YT_DLP_PATH) or not os.access(YT_DLP_PATH, os.X_OK):
    print(f"⚠️ Configured YT_DLP_PATH '{YT_DLP_PATH}' is not valid.")
    system_yt = shutil.which("yt-dlp")
    if system_yt:
        print(f"✅ Using system yt-dlp: {system_yt}")
        YT_DLP_PATH = system_yt
    else:
        print("❌ CRITICAL: No yt-dlp found!")

# --- COOKIE HANDLING ---
COOKIE_FILE = None
TEMP_COOKIE_FILE = "youtube_cookies_runtime.txt"

def setup_cookies():
    global COOKIE_FILE
    if COOKIE_FILE: return # Already setup

    env_cookies = os.environ.get("YOUTUBE_COOKIES_TXT")
    if env_cookies:
        try:
            with open(TEMP_COOKIE_FILE, "w", encoding="utf-8") as f:
                f.write(env_cookies)
            COOKIE_FILE = TEMP_COOKIE_FILE
            atexit.register(cleanup_cookies)
            log(f"🍪 Loaded cookies from secret to {TEMP_COOKIE_FILE}")
        except Exception as e:
            log(f"❌ Failed to write temp cookies: {e}")
            COOKIE_FILE = None
    elif os.path.exists("youtube_cookies.txt") and os.path.getsize("youtube_cookies.txt") > 0:
        COOKIE_FILE = "youtube_cookies.txt"
        log("🍪 Using local youtube_cookies.txt")
    else:
        COOKIE_FILE = None
        log("⚠️ No auth cookies found. API calls may fail.")

def cleanup_cookies():
    if COOKIE_FILE == TEMP_COOKIE_FILE and os.path.exists(TEMP_COOKIE_FILE):
        try:
            os.remove(TEMP_COOKIE_FILE)
            log("🧹 Cleaned up temp cookies")
        except:
            pass

def log(msg):
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute('CREATE TABLE IF NOT EXISTS synced (y_id TEXT PRIMARY KEY, title TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS publications (y_id TEXT PRIMARY KEY, title TEXT, description TEXT, rutube_status TEXT, tiktok_status TEXT, insta_status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    conn.commit()
    conn.close()

def is_video_synced(y_id, platform='rutube'):
    conn = sqlite3.connect(DB_FILE)
    column = f"{platform}_status"
    cursor = conn.execute(f'SELECT 1 FROM publications WHERE y_id=? AND {column} IS NOT NULL', (y_id,))
    exists = cursor.fetchone()
    conn.close()
    return exists is not None

def mark_video_synced(y_id, title, platform='rutube', description=None):
    conn = sqlite3.connect(DB_FILE)
    column = f"{platform}_status"
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Сначала проверяем, есть ли запись
    cursor = conn.execute('SELECT 1 FROM publications WHERE y_id=?', (y_id,))
    if cursor.fetchone():
        if description:
            conn.execute(f'UPDATE publications SET title=?, description=?, {column}=? WHERE y_id=?', 
                        (title, description, now, y_id))
        else:
            conn.execute(f'UPDATE publications SET title=?, {column}=? WHERE y_id=?', 
                        (title, now, y_id))
    else:
        conn.execute(f'INSERT INTO publications (y_id, title, description, {column}) VALUES (?, ?, ?, ?)', 
                    (y_id, title, description, now))
    
    conn.commit()
    conn.close()

def load_metadata_cache():
    """Load cached video metadata to avoid repeated API calls"""
    if os.path.exists(METADATA_CACHE_FILE):
        try:
            with open(METADATA_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_metadata_cache(cache):
    """Save video metadata cache"""
    try:
        with open(METADATA_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"⚠️ Ошибка сохранения кэша: {e}")

def get_auth_token():
    try:
        r = requests.post("https://rutube.ru/api/accounts/token_auth/", data={'username': LOGIN, 'password': PASSWORD}, timeout=20)
        return r.json().get('token') if r.status_code == 200 else None
    except Exception as e:
        log(f"⚠️ Ошибка получения токена Rutube: {e}")
        return None

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

def get_python_executable():
    """Returns path to the current or venv python executable"""
    venv_python = os.path.join(os.path.dirname(__file__), "venv", "bin", "python3")
    if os.path.exists(venv_python):
        return venv_python
    return sys.executable

def get_full_video_info(y_id, metadata_cache=None):
    """Fetches full video metadata with aggressive bypass methods"""
    
    if metadata_cache and y_id in metadata_cache:
        log(f"📄 Метадата видео {y_id} найдена в кэше")
        return metadata_cache[y_id]
    
    # Пытаемся разные комбинации клиентов для обхода блокировок
    clients = [
        "web,ios,android", # Стандартный набор с имитацией браузера
        "tv,web_embedded", # ТВ-клиенты (часто обходят "Sign in to confirm")
        "android",         # Чистый андроид
        "ios"              # Чистый iOS
    ]

    for attempt, client_list in enumerate(clients):
        try:
            cmd = [
                YT_DLP_PATH, 
                "--dump-json",
                "--no-check-certificates",
                "--extractor-args", f"youtube:player_client={client_list};player_skip=webpage,configs",
                "--js-runtimes", "deno",
                "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
            ]
            
            if COOKIE_FILE:
                cmd.extend(["--cookies", COOKIE_FILE])
                log(f"🍮 Attempt {attempt + 1}: Using cookies + clients ({client_list})")
            else:
                log(f"⚠️ Attempt {attempt + 1}: No cookies, trying clients ({client_list})")
            
            cmd.append(f"https://youtube.com/watch?v={y_id}")
            
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            
            if res.returncode == 0:
                data = json.loads(res.stdout)
                if metadata_cache is not None:
                    metadata_cache[y_id] = data
                log(f"✅ Success with client {client_list}")
                return data
            
            # Логируем конкретную ошибку для каждого метода
            error_msg = res.stderr.split('\n')[0] if res.stderr else "Unknown error"
            log(f"⚠️ Client {client_list} failed: {error_msg}")
            
        except Exception as e:
            log(f"⚠️ Error during metadata fetch: {e}")
    
    log(f"❌ All bypass methods failed for {y_id}")
    return None

def process_video(y_id, title, description, token):
    log(f"🚀 Обработка: {title}")
    local_file_base = os.path.join(UPLOADS_DIR, y_id)
    local_video_path = f"{local_file_base}.mp4"
    
    if not os.path.exists(local_video_path):
        # Используем самый надежный набор для скачивания
        yt_cmd = [
            YT_DLP_PATH, 
            "-f", "best[ext=mp4]/best", 
            "-o", f"{local_file_base}.%(ext)s",
            "--no-check-certificates",
            "--extractor-args", "youtube:player_client=tv,ios,android;player_skip=webpage,configs",
            "--js-runtimes", "deno",
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "--retries", "3"
        ]
        
        if COOKIE_FILE:
            yt_cmd.extend(["--cookies", COOKIE_FILE])
        
        yt_cmd.append(f"https://youtube.com/watch?v={y_id}")
        
        log(f"😁 Скачивание через усиленные API (tv,ios,android)...")
        result = subprocess.run(yt_cmd)

    if not os.path.exists(local_video_path) or os.path.getsize(local_video_path) == 0:
        log(f"❌ Ошибка: Видео не скачалось даже через мобильные API.")
        return False

    # --- EXTERNAL UPLOAD (Catbox) ---
    def upload_to_catbox(path):
        log(f"📦 Uploading to Catbox (External Host)...")
        try:
            files = {'reqtype': (None, 'fileupload'), 'fileToUpload': open(path, 'rb')}
            resp = requests.post("https://catbox.moe/user/api.php", files=files, timeout=300)
            if resp.status_code == 200:
                return resp.text.strip()
            log(f"❌ Catbox Error: {resp.text}")
        except Exception as e:
            log(f"❌ Catbox Exception: {e}")
        return None

    # Try external upload first
    video_url = upload_to_catbox(local_video_path)
    
    # Fallback to local server if external fails
    if not video_url:
        log("⚠️ External upload failed. Falling back to Local Server URL.")
        video_url = f"https://{PUBLIC_DOMAIN}/rutube-webhook/static/{y_id}.mp4"
    else:
        log(f"✅ External URL: {video_url}")
    # --------------------------------

    # --- RUTUBE UPLOAD ---
    if not is_video_synced(y_id, 'rutube'):
        headers = {"Authorization": f"Token {token}"}
        payload = {
            "url": video_url,
            "title": title,
            "is_hidden": False,
            "category_id": 13,
            "description": description
        }

        try:
            r = requests.post("https://rutube.ru/api/video/", json=payload, headers=headers)
            if r.status_code in [200, 201]:
                data = r.json()
                rutube_video_id = data.get('id') or data.get('video_id')
                
                if not rutube_video_id:
                    log(f"❌ ID видео не найден в ответе! Статус: {r.status_code}")
                    return False
                    
                log(f"✅ Успешно отправлено на Rutube! ID: {rutube_video_id}")
                mark_video_synced(y_id, title, 'rutube', description)
                
                # Ждем обработки и ставим кадр
                if wait_for_processing(rutube_video_id, token):
                    if set_cover_frame:
                        try:
                            set_cover_frame(rutube_video_id, title)
                        except: pass
            else:
                log(f"❌ Rutube API ошибка: {r.text}")
                return False
        except Exception as e:
            log(f"❌ Rutube API исключение: {e}")
            return False
    else:
        log("ℹ️ Видео уже есть на Rutube, проверяем соцсети...")

    # --- TIKTOK UPLOAD ---
    if not is_video_synced(y_id, 'tiktok'):
        if process_social_uploads:
            try:
                log("📱 Загрузка в TikTok...")
                # Передаем статус успеха в функцию соцсетей
                success = process_social_uploads(local_video_path, title, description)
                if success:
                    mark_video_synced(y_id, title, 'tiktok')
                    log("✅ TikTok: Успешно!")
            except Exception as e:
                log(f"⚠️ Ошибка TikTok: {e}")
    else:
        log("ℹ️ Видео уже есть в TikTok.")

        # Cleanup local file to save space
        if os.path.exists(local_video_path):
            try:
                os.remove(local_video_path)
                log(f"🗑️ Удален локальный файл: {local_video_path}")
            except Exception as e:
                log(f"⚠️ Ошибка удаления файла: {e}")

        return True
    
    return True

def sync():
    processed_count = 0
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    init_db()
    setup_cookies()
    
    # Load metadata cache at start
    metadata_cache = load_metadata_cache()
    log(f"📄 Загружен кэш с {len(metadata_cache)} видео")
    
    token = get_auth_token()
    if not token: 
        log("❌ Не удалось получить токен API")
        return False

    # Простая проверка последних видео (Видео + Shorts)
    playlists = [
        YOUTUBE_CHANNEL_URL,
        YOUTUBE_CHANNEL_URL.rstrip('/') + '/shorts'
    ]
    
    videos = []
    for playlist_url in playlists:
        log(f"🔎 Scanning playlist: {playlist_url}")
        cmd = [YT_DLP_PATH, "--dump-json", "--flat-playlist", "--playlist-end", "5"]
        if COOKIE_FILE:
             cmd.extend(["--cookies", COOKIE_FILE])
        cmd.append(playlist_url)
        
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            for line in res.stdout.strip().split("\n"):
                if line: videos.append(json.loads(line))
        else:
            log(f"⚠️ Warning: Could not scan {playlist_url}")

    if not videos:
        log("❌ Не удалось получить список видео")
        return False
    
    # 1. Проверяем top-5 (теперь из обоих списков)
    processed_this_run = 0
    for vid in videos:
        y_id = vid.get('id')
        
        # Проверяем, нужно ли делать хоть что-то (Рутуб или ТикТок)
        needs_rutube = not is_video_synced(y_id, 'rutube')
        needs_tiktok = not is_video_synced(y_id, 'tiktok')
        
        if needs_rutube or needs_tiktok:
            # Fetch full details with caching
            full_info = get_full_video_info(y_id, metadata_cache)
            
            # Если Рутуб уже готов, а ТикТок еще нет - проверяем ориентацию ДО того как считать это "работой"
            if not needs_rutube and needs_tiktok:
                width = full_info.get('width', 0)
                height = full_info.get('height', 0)
                if width > height and width > 0:
                    # log(f"📺 Пропускаем горизонтальное {y_id} для TikTok (Rutube уже есть)")
                    mark_video_synced(y_id, vid.get('title'), 'tiktok', vid.get('description'))
                    continue

            log(f"🔎 Видео {y_id} требует внимания: Rutube={needs_rutube}, TikTok={needs_tiktok}")
            
            if full_info:
                title = full_info.get('title', vid.get('title'))
                description = full_info.get('description', vid.get('description', ''))
            else:
                title = vid.get('title')
                description = vid.get('description', '')
            
            result = process_video(y_id, title, description, token)
            save_metadata_cache(metadata_cache)
            
            if result is False:
                log(f"❌ Failed to process video {y_id}")
                return False
            
            processed_this_run += 1
            if needs_rutube:
                # Если загружали на Рутуб, то 1 за раз (лимит)
                return True
            
            if processed_this_run >= 3:
                # Если только соцсети - до 3 за раз
                return True

    # Если мы здесь, значит все top-5 уже синхронизированы.
    if not videos:
        log("⚠️ Не найдено видео на канале (список пуст).")
        return True

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
            log(f"🕵️ Последнее видео было {days_diff} дн. назад. Расширяем поиск...")
    else:
        should_expand = True
    
    if should_expand:
        # 3. Расширенный поиск (50 видео)
        cmd_expanded = [YT_DLP_PATH, "--dump-json", "--flat-playlist", "--playlist-end", "50"]
        if COOKIE_FILE:
            cmd_expanded.extend(["--cookies", COOKIE_FILE])
        cmd_expanded.append(YOUTUBE_CHANNEL_URL)
        
        res_expanded = subprocess.run(cmd_expanded, capture_output=True, text=True)
        
        expanded_videos = []
        for line in res_expanded.stdout.strip().split("\n"):
            if line: expanded_videos.append(json.loads(line))
        
        for vid in expanded_videos:
            if processed_count >= 3:
                log("🛑 Достигнут лимит (3 видео) за один запуск.")
                break

            y_id = vid.get('id')
            if not is_video_synced(y_id):
                log(f"🕰️ Найдено старое несинхронизированное видео: {vid.get('title')}")
                
                full_info = get_full_video_info(y_id, metadata_cache)
                if full_info:
                    title = full_info.get('title', vid.get('title'))
                    description = full_info.get('description', vid.get('description', ''))
                else:
                    title = vid.get('title')
                    description = vid.get('description', '')
                
                result = process_video(y_id, title, description, token)
                save_metadata_cache(metadata_cache)
                if result:
                    processed_count += 1
                else:
                    log(f"❌ Failed to process old video {y_id}")
                    return False
        
        if processed_count > 0:
            return True
        
        log("✅ Все видео из последних 50 уже синхронизированы.")
    else:
        log("✅ Все последние видео синхронизированы.")
    
    # Save cache before exit
    save_metadata_cache(metadata_cache)
    return True

if __name__ == "__main__":
    success = sync()
    if success is False:
        log("❌ Sync finished with errors.")
        sys.exit(1)
    log("✅ Sync finished successfully.")
    sys.exit(0)
