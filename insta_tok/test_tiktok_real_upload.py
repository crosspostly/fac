import os
import sys
from tiktok_uploader.upload import upload_video
from tiktok_uploader.browsers import chrome_defaults
# Patch for Linux chromedriver
from tiktok_uploader.browsers import services
from selenium.webdriver.chrome.service import Service
import platform

if platform.system() == "Linux":
    services["chrome"] = lambda: Service(executable_path="/usr/bin/chromedriver")

# Path to a real video file
VIDEO_PATH = "../uploads/test_video.mp4"
COOKIES_FILE = "tiktok_cookies.txt"
CAPTION = "Test upload from CLI bot. #test #bot"

if not os.path.exists(VIDEO_PATH):
    print(f"❌ Video not found: {VIDEO_PATH}")
    # Fallback to create a dummy video if test_video is missing? 
    # No, user has test_video.mp4 in the list.
    sys.exit(1)

print(f"🚀 Starting test upload to TikTok...")
print(f"Video: {VIDEO_PATH}")
print(f"Cookies: {COOKIES_FILE}")

try:
    options = chrome_defaults(headless=True)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Upload
    failed_list = upload_video(
        filename=VIDEO_PATH,
        description=CAPTION,
        cookies=COOKIES_FILE,
        headless=True,
        options=options
    )

    if not failed_list:
        print("✅ TikTok upload successful!")
    else:
        print(f"❌ TikTok upload failed: {failed_list}")

except Exception as e:
    print(f"❌ Exception: {e}")
