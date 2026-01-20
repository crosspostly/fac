# -*- coding: utf-8 -*-
import os
import sys
from dotenv import load_dotenv

# Add current dir to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from insta_tok.instagram_poster_lib import InstagramPoster

# Load env from insta_tok subfolder
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, "insta_tok", ".env")
load_dotenv(env_path)

INSTA_USERNAME = os.getenv("INSTA_USERNAME")
INSTA_PASSWORD = os.getenv("INSTA_PASSWORD")
SESSION_FILE = os.path.join(current_dir, "insta_tok", "instagram_session.json")

print(f"Testing login for user: {INSTA_USERNAME} using session {SESSION_FILE}")

try:
    poster = InstagramPoster(INSTA_USERNAME, INSTA_PASSWORD, SESSION_FILE)
    if poster.login():
        print("✅ Login SUCCESSFUL via session or password!")
        info = poster.client.user_info(poster.client.user_id)
        print(f"User info: {info.username} (PK: {info.pk})")
    else:
        print("❌ Login FAILED!")
        sys.exit(1)
    
except Exception as e:
    print(f"❌ Exception during test: {e}")
    sys.exit(1)
