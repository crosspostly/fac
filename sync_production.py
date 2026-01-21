# -*- coding: utf-8 -*-
import os
import requests
import subprocess
import time
import datetime
import json
import sqlite3
import shutil
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

def get_full_video_info(y_id, metadata_cache=None):
    """Fetches full video metadata with caching and retry logic"""
    
    # Check cache first
    if metadata_cache and y_id in metadata_cache:
        log(f"📄 Метадата видео {y_id} найдена в кэше")
        return metadata_cache[y_id]
    
    for attempt in range(3):
        try:
            cmd = [YT_DLP_PATH, "--dump-json"]
            
            # Critical: pass cookies for YouTube authentication
            if os.path.exists("youtube_cookies.txt"):
                cmd.extend(["--cookies", "youtube_cookies.txt"])
                log(f"🍮 Using YouTube cookies for attempt {attempt + 1}...")
            else:
                log(f"⚠️ No YouTube cookies found! Attempt {attempt + 1} will likely fail.")
            
            cmd.append(f"https://youtube.com/watch?v={y_id}")
            
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if res.returncode == 0:
                data = json.loads(res.stdout)
                # Cache successful result
                if metadata_cache is not None:
                    metadata_cache[y_id] = data
                log(f"✅ Получена полная инфо для {y_id}")
                return data
            else:
                if "Sign in to confirm" in res.stderr or "bot" in res.stderr.lower():
                    log(f"❌ YouTube требует авторизацию! Cookies истекли или невалидны.")
                    log(f"📄 Обнови YOUTUBE_COOKIES_TXT secret в GitHub!")
                else:
                    log(f"⚠️ Ошибка (attempt {attempt + 1}/3): {res.stderr[:200]}")
                
                if attempt < 2:
                    wait_time = (2 ** attempt) * 5  # Exponential backoff: 5s, 10s, 20s
                    log(f"⏳ Ожидаю {wait_time}s перед повторным попытом...")
                    time.sleep(wait_time)
        
        except subprocess.TimeoutExpired:
            log(f"⚠️ Timeout при получении инфо (attempt {attempt + 1}/3)")
        except Exception as e:
            log(f"⚠️ Ошибка: {e} (attempt {attempt + 1}/3)")
    
    log(f"❌ Не удалось получить полную инфо для {y_id} после 3 попыток")
    return None

def process_video(y_id, title, description, token):
    log(f"🚀 Обработка: {title}")
    local_file_base = os.path.join(UPLOADS_DIR, y_id)
    local_video_path = f"{local_file_base}.mp4"
    local_thumb_path = f"{local_file_base}.jpg"
    
    # Скачивание (только видео)
    if not os.path.exists(local_video_path):
        yt_cmd = [YT_DLP_PATH, "-f", "best[ext=mp4]", "-o", f"{local_file_base}.%(ext)s"]
        
        # CRITICAL: Use cookies for authentication
        if os.path.exists("youtube_cookies.txt"):
            yt_cmd.extend(["--cookies", "youtube_cookies.txt"])
            log(f"🍮 Скачивание с cookies...")
        else:
            log(f"⚠️ Нет cookies! Скачивание без авторизации (может не работать)...")
        
        yt_cmd.extend(["--retries", "5", "--fragment-retries", "5"])
        yt_cmd.append(f"https://youtube.com/watch?v={y_id}")
        
        log(f"😁 Начинаю скачивание...")
        result = subprocess.run(yt_cmd)

    if not os.path.exists(local_video_path):
        log(f"❌ Ошибка: Файл не скачался! Проблемы:")
        log(f"   • YouTube требует авторизацию (обновить cookies)")
        log(f"   • GitHub Actions IP заблокирован YouTube")
        log(f"   • Видео недоступно в вашем регионе")
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
            
        log(f"✅ Успешно отправлено на Rutube! ID: {rutube_video_id}")
        
        # Ждем обработки
        if wait_for_processing(rutube_video_id, token):
            log("✅ Rutube: Видео обработано.")
            
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
        if process_social_uploads:
            try:
                log("📱 Начинаю загрузку в соцсети (TikTok/Instagram)...")
                success = process_social_uploads(local_video_path, title, description)
                if success:
                    log("✅ Соцсети: Успешно!")
                else:
                    log("⚠️ Соцсети: Ошибка не наша, но загрузка могла быть провалена")
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
    log(f"❌ Rutube API ошибка: {r.text}")
    return False

def sync():
    init_db()
    
    # Load metadata cache at start
    metadata_cache = load_metadata_cache()
    log(f"📄 Загружен кэш с {len(metadata_cache)} видео")
    
    token = get_auth_token()
    if not token: 
        log("❌ Не удалось получить токен API")
        return False

    # Простая проверка последних видео
    cmd = [YT_DLP_PATH, "--dump-json", "--flat-playlist", "--playlist-end", "5"]
    if os.path.exists("youtube_cookies.txt"):
         cmd.extend(["--cookies", "youtube_cookies.txt"])
    cmd.append(YOUTUBE_CHANNEL_URL)
    
    res = subprocess.run(cmd, capture_output=True, text=True)

    if res.returncode != 0:
        log(f"❌ Ошибка исполнения YT-DLP (Exit Code: {res.returncode})")
        log(f"📝 Stderr: {res.stderr[:300]}")
        return False
    
    videos = []
    try:
        for line in res.stdout.strip().split("\n"):
            if line: videos.append(json.loads(line))
    except json.JSONDecodeError as e:
        log(f"❌ Ошибка парсинга JSON: {e}")
        return False
    
    # 1. Проверяем top-5
    for vid in videos:
        y_id = vid.get('id')
        if not is_video_synced(y_id):
            # Fetch full details with caching
            full_info = get_full_video_info(y_id, metadata_cache)
            if full_info:
                title = full_info.get('title', vid.get('title'))
                description = full_info.get('description', vid.get('description', ''))
            else:
                title = vid.get('title')
                description = vid.get('description', '')
                log(f"⚠️ Using fallback metadata for {y_id}")
            
            result = process_video(y_id, title, description, token)
            # Save cache after processing
            save_metadata_cache(metadata_cache)
            return result

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
        if os.path.exists("youtube_cookies.txt"):
            cmd_expanded.extend(["--cookies", "youtube_cookies.txt"])
        cmd_expanded.append(YOUTUBE_CHANNEL_URL)
        
        res_expanded = subprocess.run(cmd_expanded, capture_output=True, text=True)
        
        expanded_videos = []
        for line in res_expanded.stdout.strip().split("\n"):
            if line: expanded_videos.append(json.loads(line))
        
        for vid in expanded_videos:
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
                return result
        
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
