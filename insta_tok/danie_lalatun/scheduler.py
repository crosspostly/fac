import os
import sys
import json
import random
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Add the directory containing instagram_poster.py to the Python path
# This allows importing InstagramPoster class directly.
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from instagram_poster import InstagramPoster
    from instagrapi.exceptions import ClientError, PleaseWaitFewMinutes, LoginRequired
except ImportError as e:
    logging.error(f"Failed to import InstagramPoster from instagram_poster.py: {e}")
    logging.error("Please ensure instagram_poster.py is in the same directory.")
    sys.exit(1)


# Configuration
CONTENT_DIR = Path("content/")
POSTED_CONTENT_FILE = "danie_lalatun_posted_content.json"
USERNAME_ENV = "INSTAGRAM_USERNAME_DANIE_LALATUN"
PASSWORD_ENV = "INSTAGRAM_PASSWORD_DANIE_LALATUN"
POSTING_INTERVAL_DAYS = 2 # Post every X days

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('instagram_poster.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_posted_content():
    """Loads the record of posted content."""
    if Path(POSTED_CONTENT_FILE).exists():
        try:
            with open(POSTED_CONTENT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Error decoding {POSTED_CONTENT_FILE}, creating a new one.")
            return {"posted_files": [], "last_post_date": None}
    return {"posted_files": [], "last_post_date": None}

def save_posted_content(data):
    """Saves the record of posted content."""
    with open(POSTED_CONTENT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def get_unposted_content(posted_files):
    """
    Returns a list of unposted content files from CONTENT_DIR.
    Prioritizes images over videos.
    """
    if not CONTENT_DIR.is_dir():
        logger.error(f"Content directory not found: {CONTENT_DIR}")
        return []

    all_content = [f for f in CONTENT_DIR.iterdir() if f.is_file() and f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.mp4', '.mov']]
    unposted = [f for f in all_content if str(f) not in posted_files]

    if not unposted:
        logger.info("All content has been posted. Waiting for new content.")
        return [] # Don't reset list automatically to avoid loops

    # Separate images and videos
    images = [f for f in unposted if f.suffix.lower() in ['.jpg', '.jpeg', '.png']]
    videos = [f for f in unposted if f.suffix.lower() in ['.mp4', '.mov']]

    # Prioritize images
    if images:
        return images
    return videos # If no images, return videos

def generate_random_post_time(start_datetime: datetime) -> datetime:
    """Generates a random datetime within the next 24 hours from start_datetime."""
    # Generate a random delay in seconds within a 24-hour window
    random_seconds = random.randint(0, 24 * 3600 - 1)
    return start_datetime + timedelta(seconds=random_seconds)

def main():
    if Path("PAUSED").exists():
        logger.warning("Scheduler is PAUSED by user. Exiting.")
        sys.exit(0)

    load_dotenv()

    username = os.getenv(USERNAME_ENV)
    password = os.getenv(PASSWORD_ENV)

    if not username or not password:
        logger.error(f"Environment variables {USERNAME_ENV} and {PASSWORD_ENV} not set in .env file.")
        sys.exit(1)

    posted_data = load_posted_content()
    last_post_date_str = posted_data.get("last_post_date")
    last_post_date = datetime.fromisoformat(last_post_date_str) if last_post_date_str else None

    now = datetime.now()

    # Determine if it's time to consider posting
    should_post_today = False
    if last_post_date is None:
        logger.info("No previous post found. Will attempt to post.")
        should_post_today = True
    else:
        time_since_last_post = now - last_post_date
        if time_since_last_post >= timedelta(days=POSTING_INTERVAL_DAYS):
            logger.info(f"It's been {time_since_last_post.days} days since the last post. Ready to post.")
            should_post_today = True
        else:
            logger.info(f"Less than {POSTING_INTERVAL_DAYS} days since last post. Skipping. (Last post: {last_post_date.isoformat()})")

    if not should_post_today:
        return

    # Check if a target random post time has been set for the current interval
    target_post_time_str = posted_data.get("target_post_time")
    target_post_time = datetime.fromisoformat(target_post_time_str) if target_post_time_str else None

    if target_post_time is None or (last_post_date and target_post_time < last_post_date):
        # If no target time or target time is older than last post, generate a new one
        target_post_time = generate_random_post_time(now)
        posted_data["target_post_time"] = target_post_time.isoformat()
        save_posted_content(posted_data)
        logger.info(f"Generated new target post time: {target_post_time.isoformat()}")

    if now < target_post_time:
        logger.info(f"Waiting for target post time: {target_post_time.isoformat()}. Current time: {now.isoformat()}")
        return

    logger.info(f"Current time ({now.isoformat()}) is past target post time ({target_post_time.isoformat()}). Proceeding with post.")

    unposted_files = get_unposted_content(posted_data["posted_files"])

    if not unposted_files:
        logger.info("No content to post. Exiting.")
        return

    file_to_post = random.choice(unposted_files)
    logger.info(f"Selected file for posting: {file_to_post}")

    session_file_name = f"session_{username}.json"
    poster = InstagramPoster(username, password, session_file=session_file_name)

    try:
        if not poster.login():
            logger.error("Failed to login to Instagram.")
            sys.exit(1)

        result = None
        # Simplified caption for now, could be dynamic
        caption = f"🔥 New update from danie_lalatun! Check it out! #{file_to_post.stem}"

        if file_to_post.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            result = poster.upload_photo(str(file_to_post), caption)
        elif file_to_post.suffix.lower() in ['.mp4', '.mov']:
            result = poster.upload_video(str(file_to_post), caption)
        else:
            logger.error(f"Unsupported file type for posting: {file_to_post.suffix}")

        if result:
            logger.info(f"Successfully posted {file_to_post}. Post ID: {result.get('pk')}, URL: https://www.instagram.com/p/{result.get('code')}/")
            posted_data["posted_files"].append(str(file_to_post))
            posted_data["last_post_date"] = now.isoformat() # Record current time as last post time
            # Clear target_post_time as it's been met
            posted_data["target_post_time"] = None
            save_posted_content(posted_data)
        else:
            logger.error(f"Failed to post {file_to_post}.")

    except PleaseWaitFewMinutes:
        logger.critical("Instagram rate limit detected (PleaseWaitFewMinutes). Exiting immediately.")
        sys.exit(1)
    except ClientError as e:
        logger.error(f"Instagram API client error: {e}")
        if "403" in str(e) or "401" in str(e):
             logger.critical("Auth/Permission error detected (403/401). Exiting immediately.")
             sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")


main()