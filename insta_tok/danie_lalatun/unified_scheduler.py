import os
import sys
import json
import random
import time
import logging
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Ensure we can import modules from the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from instagram_poster import InstagramPoster
    from instagrapi.exceptions import ClientError, PleaseWaitFewMinutes
except ImportError as e:
    logging.error(f"Failed to import modules: {e}")
    sys.exit(1)

# --- CONFIGURATION ---
CONTENT_DIR = Path("content/")  # Relative to where script is run
POSTED_CONTENT_FILE = "unified_posted_content.json"
USERNAME_ENV = "INSTAGRAM_USERNAME_DANIE_LALATUN"
PASSWORD_ENV = "INSTAGRAM_PASSWORD_DANIE_LALATUN"
TIKTOK_COOKIES_FILE = "tiktok_cookies.txt"

# Post Interval Settings
POSTING_INTERVAL_HOURS = 24  # Post every 24 hours (approx)
RANDOM_DELAY_MINUTES = 60    # Plus random delay up to 60 mins

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unified_scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("UnifiedScheduler")

def load_posted_content():
    if Path(POSTED_CONTENT_FILE).exists():
        try:
            with open(POSTED_CONTENT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"posted_files": [], "last_post_date": None}
    return {"posted_files": [], "last_post_date": None}

def save_posted_content(data):
    with open(POSTED_CONTENT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def get_unposted_content(posted_files):
    if not CONTENT_DIR.is_dir():
        logger.error(f"Content directory not found: {CONTENT_DIR}")
        return []

    # Recursive search for content files
    all_content = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.mp4', '*.mov']:
        all_content.extend(CONTENT_DIR.rglob(ext))

    # Filter out likely thumbnails (e.g. video.mp4.jpg)
    valid_content = [f for f in all_content if not str(f).endswith('.mp4.jpg')]

    unposted = [f for f in valid_content if str(f) not in posted_files]
    
    if not unposted:
        logger.info("All content has been posted.")
        return []
    
    return unposted

def post_to_tiktok(video_path, caption):
    """Executes the publish.py script to upload to TikTok."""
    logger.info(f"Attempting to upload to TikTok: {video_path}")
    
    if not Path(TIKTOK_COOKIES_FILE).exists():
        logger.error(f"TikTok cookies not found at {TIKTOK_COOKIES_FILE}. Skipping TikTok.")
        return False

    # Command: python publish.py "video_path" "caption"
    # We assume python executable is the same as current process
    python_exe = sys.executable
    script_path = os.path.join(current_dir, "publish.py")
    
    cmd = [python_exe, script_path, str(video_path), caption]
    
    try:
        # Run process and capture output
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        logger.info(f"TikTok Script Output:\n{result.stdout}")
        
        if result.returncode == 0 and "successfully published" in result.stdout.lower():
            logger.info("TikTok upload SUCCESSFUL.")
            return True
        else:
            logger.error(f"TikTok upload FAILED. Stderr: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error running TikTok script: {e}")
        return False

def main():
    if Path("PAUSED").exists():
        logger.warning("Scheduler is PAUSED by user. Exiting.")
        sys.exit(0)

    load_dotenv()
    
    # 1. Check Credentials
    ig_user = os.getenv(USERNAME_ENV)
    ig_pass = os.getenv(PASSWORD_ENV)
    
    if not ig_user or not ig_pass:
        logger.warning("Instagram credentials not found in .env. Instagram posting will fail.")
        # We don't exit, maybe user just wants TikTok? 
        # But this is a unified scheduler... let's enforce both or warn.
    
    # 2. Check Schedule
    posted_data = load_posted_content()
    last_post_str = posted_data.get("last_post_date")
    
    if last_post_str:
        last_post_date = datetime.fromisoformat(last_post_str)
        next_post_window = last_post_date + timedelta(hours=POSTING_INTERVAL_HOURS)
        
        if datetime.now() < next_post_window:
            logger.info(f"Not time to post yet. Next window starts: {next_post_window}")
            return
    else:
        logger.info("No previous posts found. Posting immediately.")

    # 3. Select Content
    unposted = get_unposted_content(posted_data["posted_files"])
    if not unposted:
        logger.info("No new content found.")
        return

    # Pick random file
    file_to_post = random.choice(unposted)
    file_path = str(file_to_post)
    logger.info(f"Selected content: {file_path}")
    
    # Generate Caption (Simple for now)
    caption = f"New AI Art Drop! 🤖✨ #{file_to_post.stem.replace(' ', '')} #AI #DigitalArt #Future"
    
    success_ig = False
    success_tt = False

    # 4. Post to Instagram
    if ig_user and ig_pass:
        poster = InstagramPoster(ig_user, ig_pass, session_file="instagram_session.json")
        if poster.login():
            try:
                if file_to_post.suffix.lower() in ['.mp4', '.mov']:
                    res = poster.upload_video(file_path, caption)
                else:
                    res = poster.upload_photo(file_path, caption)
                
                if res:
                    success_ig = True
                    logger.info("Instagram post success.")
            except Exception as e:
                logger.error(f"Instagram upload failed: {e}")
        else:
            logger.error("Instagram login failed.")

            # 5. Post to TikTok (Video Only) - DISABLED

            # if file_to_post.suffix.lower() in ['.mp4', '.mov']:

            #     success_tt = post_to_tiktok(file_path, caption)

            # else:

            #     logger.info("Skipping TikTok (not a video file).")

            #     success_tt = True 

            success_tt = True 

    

        # 6. Update Log

        # We mark as posted if AT LEAST ONE platform succeeded to avoid getting stuck on a file 

        # that is valid for one platform but invalid for another (e.g. format issue)

        if success_ig or success_tt:

            posted_data["posted_files"].append(file_path)

            posted_data["last_post_date"] = datetime.now().isoformat()

            save_posted_content(posted_data)

            logger.info(f"Marked {file_path} as posted (IG: {success_ig}, TT: {success_tt}).")

        else:

            logger.error("Both platforms failed. File NOT marked as posted. Will retry next run.")

if __name__ == "__main__":
    main()
