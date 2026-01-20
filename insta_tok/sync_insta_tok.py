#!/usr/bin/env python3
import os
import sys
import datetime
import time
import subprocess
import json
import sqlite3
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
INSTA_USERNAME = os.getenv("INSTA_USERNAME")
INSTA_PASSWORD = os.getenv("INSTA_PASSWORD")
YOUTUBE_CHANNEL_URL = "https://www.youtube.com/channel/UC8hbIF2zfPI5KwlZ2Zq5RmQ"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "sync.db")
TIKTOK_COOKIES_FILE = os.path.join(BASE_DIR, "tiktok_cookies.txt")
YT_DLP_PATH = os.path.abspath(os.path.join(BASE_DIR, "../yt-dlp")) # Assuming it's in parent dir
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")

# Ensure download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def log(msg):
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute('CREATE TABLE IF NOT EXISTS synced (y_id TEXT PRIMARY KEY, title TEXT, tiktok_status TEXT, insta_status TEXT)')
    conn.commit()
    conn.close()

def is_video_synced(y_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.execute('SELECT tiktok_status, insta_status FROM synced WHERE y_id=?', (y_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        # If both are success or skipped, we consider it synced.
        # But maybe we want to retry if one failed?
        # For now, if record exists, we assume we tried. 
        # To be more robust, we could check if both are 'success'.
        # Let's return True if the record exists to avoid re-processing indefinitely in this simple version.
        return True 
    return False

def mark_video_synced(y_id, title, tiktok_status, insta_status):
    conn = sqlite3.connect(DB_FILE)
    conn.execute('INSERT OR REPLACE INTO synced VALUES (?, ?, ?, ?)', (y_id, title, tiktok_status, insta_status))
    conn.commit()
    conn.close()

def download_video(y_id):
    log(f"⬇️ Downloading video {y_id}...")
    file_base = os.path.join(DOWNLOAD_DIR, y_id)
    # Output template: id.mp4
    cmd = [YT_DLP_PATH, "-f", "best[ext=mp4]"]
    if os.path.exists("../youtube_cookies.txt"): cmd.insert(1, "--cookies"); cmd.insert(2, "../youtube_cookies.txt")
    # OLD: cmd = [YT_DLP_PATH, "-f", "best[ext=mp4]", "-o", f"{file_base}.%(ext)s", f"https://youtube.com/watch?v={y_id}"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        video_path = f"{file_base}.mp4"
        if os.path.exists(video_path):
            return video_path
    log(f"❌ Download failed: {res.stderr}")
    return None

def upload_to_tiktok(video_path, caption):
    log("🎵 Uploading to TikTok...")
    try:
        # Import here to avoid dependency issues if not installed
        from tiktok_uploader.upload import upload_video
        from tiktok_uploader.browsers import chrome_defaults, services
        from selenium.webdriver.chrome.service import Service
        import platform

        if platform.system() == "Linux":
            services["chrome"] = lambda: Service(executable_path="/usr/bin/chromedriver")
        
        if not os.path.exists(TIKTOK_COOKIES_FILE):
            log(f"⚠️ TikTok cookies not found at {TIKTOK_COOKIES_FILE}")
            return "failed_no_cookies"

        options = chrome_defaults(headless=True)
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        # Determine strictness. If we want to retry on failure, we return False/None.
        # The library returns failed uploads list or empty list if success.
        failed_list = upload_video(
            filename=video_path,
            description=caption,
            cookies=TIKTOK_COOKIES_FILE,
            headless=True,
            options=options
        )

        if not failed_list:
            log("✅ TikTok upload successful")
            return "success"
        else:
            log(f"❌ TikTok upload failed: {failed_list}")
            return "failed"
            
    except Exception as e:
        log(f"❌ TikTok upload exception: {e}")
        return f"error_{str(e)}"

def upload_to_instagram(video_path, caption):
    log("📸 Uploading to Instagram...")
    try:
        from instagrapi import Client
        cl = Client()
        try:
            cl.login(INSTA_USERNAME, INSTA_PASSWORD)
        except Exception as e:
             # Try 2FA or challenge handling if needed, but for now basic login
             log(f"❌ Instagram login failed: {e}")
             return "login_failed"

        media = cl.clip_upload(
            video_path,
            caption=caption
        )
        if media:
            log(f"✅ Instagram upload successful: {media.pk}")
            return "success"
        else:
            log("❌ Instagram upload returned no media")
            return "failed"
            
    except Exception as e:
        log(f"❌ Instagram upload exception: {e}")
        return f"error_{str(e)}"

def sync():
    init_db()
    
    # Check top 5 videos
    cmd = [YT_DLP_PATH, "--dump-json", "--flat-playlist", "--playlist-end", "5", YOUTUBE_CHANNEL_URL]
    res = subprocess.run(cmd, capture_output=True, text=True)
    
    videos = []
    for line in res.stdout.strip().split("\n"):
        if line: videos.append(json.loads(line))
        
    for vid in videos:
        y_id = vid.get('id')
        title = vid.get('title', 'No Title')
        
        if is_video_synced(y_id):
            continue
            
        log(f"🆕 Found new video: {title} ({y_id})")
        
        # Get full description for caption
        full_desc = ""
        try:
            desc_cmd = [YT_DLP_PATH, "--dump-json", f"https://youtube.com/watch?v={y_id}"]
            desc_res = subprocess.run(desc_cmd, capture_output=True, text=True)
            if desc_res.returncode == 0:
                full_info = json.loads(desc_res.stdout)
                full_desc = full_info.get('description', '')
        except Exception as e:
            log(f"⚠️ Could not fetch full description: {e}")
            
        # Create a caption (limit length if needed, hashtags etc)
        # For now just title + some tags or first few lines of description
        caption = f"{title}\n\n{full_desc[:500]}..." if len(full_desc) > 500 else f"{title}\n\n{full_desc}"
        
        video_path = download_video(y_id)
        if video_path:
            tiktok_status = upload_to_tiktok(video_path, caption)
            # insta_status = upload_to_instagram(video_path, caption)
            insta_status = "disabled"
            
            mark_video_synced(y_id, title, tiktok_status, insta_status)
            
            # Cleanup
            try:
                os.remove(video_path)
            except:
                pass
            
            # Process only one new video per run to avoid spamming/rate limits
            return

    log("✅ No new videos to sync.")

if __name__ == "__main__":
    sync()
