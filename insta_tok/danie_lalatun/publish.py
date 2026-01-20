#!/usr/bin/env python3
"""
TikTok Publisher - Минимальная версия

Этот скрипт объединяет функциональность всех предыдущих скриптов
в одном файле с возможностью выбора метода публикации.
"""

import os
import sys
import time
from datetime import datetime

def publish_with_tiktok_uploader(video_path, caption, cookies_path='./tiktok_cookies.txt', headless=False):
    """
    Publish video using tiktok-uploader
    """
    try:
        from tiktok_uploader.upload import upload_video
        from tiktok_uploader.browsers import chrome_defaults, services
        from selenium.webdriver.chrome.service import Service
        import platform

        # Patch services to use system chromedriver (Linux only)
        if platform.system() == "Linux":
            services["chrome"] = lambda: Service(executable_path="/usr/bin/chromedriver")

        # Check if cookies file exists
        if os.path.exists(cookies_path):
            print(f"[OK] Cookies file found: {cookies_path}")
        else:
            print(f"[ERROR] Cookies file not found: {cookies_path}")
            return False

        # Check if video file exists
        if not os.path.exists(video_path):
            print(f"[ERROR] Video file not found: {video_path}")
            return False

        print(f"[OK] Video file found: {video_path}")
        print(f"Caption: {caption}")

        # Prepare options
        options = chrome_defaults(headless=headless)
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--window-size=1920,1080")

        # Upload video with cookies
        print(f"[INFO] Starting upload... Browser visible for troubleshooting")
        result = upload_video(
            filename=video_path,
            description=caption,
            cookies=cookies_path,  # Pass cookies file directly
            headless=False,  # Force visible browser to troubleshoot
            options=options
        )

        if not result:
            print("[SUCCESS] Video successfully published to TikTok!")
            return True
        else:
            print(f"[ERROR] Failed to publish video. Failed list: {result}")
            return False

    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        print("Install: pip install tiktok-uploader")
        return False
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[ERROR] Upload error: {e}")
        return False


def main():
    print("TikTok Publisher - Minimal Version")
    print("="*50)
    print("[INFO] Browser will be visible for tracking the process")
    print()

    # Check for cookies file
    cookies_file = './tiktok_cookies.txt'
    if not os.path.exists(cookies_file):
        print(f"[ERROR] Cookies file not found: {cookies_file}")
        print("   This file is necessary for authentication with TikTok.")
        print("   Make sure you have valid cookies from your account.")
        return False

    # Default parameters
    default_video_path = './danie_lalatun/Week_1/Day_3_Slideshow/final_merged_selfie.mp4'
    default_caption = 'Amazing AI-generated content! #ai #artificialintelligence #tech #aigenerated #digitalart'

    # Get parameters from command line
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        video_path = default_video_path

    if len(sys.argv) > 2:
        caption = sys.argv[2]
    else:
        caption = default_caption

    print(f"Video: {video_path}")
    print(f"Caption: {caption}")
    print()

    # Publish with visible browser
    success = publish_with_tiktok_uploader(video_path, caption, headless=True)

    if success:
        print("\n[SUCCESS] Publishing completed successfully!")
        print("   Check your TikTok profile to confirm the publication.")
    else:
        print("\n[ERROR] Publishing failed!")
        print("\n[INFO] Tips:")
        print("   - Make sure tiktok_cookies.txt contains valid cookies")
        print("   - Check that the video file exists and is accessible")
        print("   - Install dependencies: pip install -r requirements.txt")

    return success


if __name__ == "__main__":
    main()