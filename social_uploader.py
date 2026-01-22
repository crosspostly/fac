# -*- coding: utf-8 -*-
import os
import sys
import datetime
import logging
import subprocess
import json
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env from insta_tok subfolder
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, "insta_tok", ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)

TIKTOK_COOKIES_FILE = os.path.join(current_dir, "insta_tok", "tiktok_cookies.txt")

# Instagram отключен по просьбе пользователя
# INSTA_USERNAME = os.getenv("INSTA_USERNAME")
# INSTA_PASSWORD = os.getenv("INSTA_PASSWORD")
# INSTA_SESSION_FILE = os.path.join(current_dir, "insta_tok", "pp_witch_session.json")

def log(msg):
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def get_video_orientation(video_path):
    """
    Returns 'vertical', 'horizontal', or 'square' based on resolution.
    Uses ffprobe via yt-dlp helper or direct ffprobe.
    """
    try:
        # Using ffprobe directly if available
        cmd = [
            "ffprobe", 
            "-v", "error", 
            "-select_streams", "v:0", 
            "-show_entries", "stream=width,height", 
            "-of", "json", 
            video_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            info = json.loads(res.stdout)
            width = int(info['streams'][0]['width'])
            height = int(info['streams'][0]['height'])
            
            if height > width:
                return 'vertical'
            elif width > height:
                return 'horizontal'
            else:
                return 'square'
    except Exception as e:
        log(f"⚠️ Could not detect orientation (ffprobe error): {e}")
    
    return 'unknown' # Default fallback

# Duplicate check logic
POSTED_LOG_FILE = os.path.join(current_dir, "insta_tok", "tiktok_posted.json")

def load_posted_files():
    if os.path.exists(POSTED_LOG_FILE):
        try:
            with open(POSTED_LOG_FILE, 'r') as f:
                data = json.load(f)
                return set(data.get('posted_files', []))
        except:
            return set()
    return set()

def save_posted_file(filename):
    posted = load_posted_files()
    posted.add(str(filename))
    with open(POSTED_LOG_FILE, 'w') as f:
        json.dump({
            "posted_files": list(posted),
            "last_update": str(datetime.datetime.now())
        }, f, indent=4)

def upload_to_tiktok(video_path, caption):
    log("🎵 TikTok upload initiated...")
    
    # Check for duplicates
    posted = load_posted_files()
    if str(video_path) in posted:
        log(f"⚠️ Video already posted to TikTok (found in log): {video_path}")
        return True

    if not os.path.exists(TIKTOK_COOKIES_FILE):
        log(f"⚠️ TikTok cookies not found at {TIKTOK_COOKIES_FILE}")
        return False

    try:
        # Добавляем путь к виртуальному окружению, если пакеты там
        sys.path.append(os.path.join(current_dir, "insta_tok"))
        
        from tiktok_uploader.upload import upload_video
        from tiktok_uploader.browsers import chrome_defaults, services
        from selenium.webdriver.chrome.service import Service
        import platform

        if platform.system() == "Linux":
            services["chrome"] = lambda: Service(executable_path="/usr/bin/chromedriver")
        
        options = chrome_defaults(headless=True)
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        # Увеличиваем таймауты
        # (Они заданы в config.toml библиотеки, но мы их уже пропатчили)

        log("🚀 Starting upload via tiktok-uploader...")
        failed_list = upload_video(
            filename=video_path,
            description=caption,
            cookies=TIKTOK_COOKIES_FILE,
            headless=True,
            options=options
        )

        if not failed_list:
            log("✅ TikTok upload successful!")
            save_posted_file(video_path)
            return True
        else:
            log(f"❌ TikTok upload failed: {failed_list}")
            return False
            
    except Exception as e:
        log(f"❌ TikTok upload exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def process_social_uploads(video_path, title, description):
    """
    Main entry point for social uploads.
    Called by sync_production.py after Rutube upload.
    """
    log(f"🕵️ Analyzing video for social media: {title}")
    
    orientation = get_video_orientation(video_path)
    log(f"📐 Video orientation: {orientation}")

    if orientation == 'vertical':
        log("📱 Vertical video detected. Sending to TikTok...")
        
        # Caption strategy: Use ONLY description if available to avoid title duplication
        # Fallback to title only if description is missing.
        if description and description.strip():
            caption = description[:2000]
        else:
            caption = title
        
        return upload_to_tiktok(video_path, caption)
    else:
        log("📺 Horizontal video detected. Skipping TikTok (Shorts only).")
        return True

    