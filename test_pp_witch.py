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
# NO SESSION FILE for this test
SESSION_FILE = os.path.join(current_dir, "insta_tok", "pp_witch_session.json")

print(f"Testing login for user: {INSTA_USERNAME} (NO PREVIOUS SESSION)")

try:
    poster = InstagramPoster(INSTA_USERNAME, INSTA_PASSWORD, SESSION_FILE)
    if poster.login():
        print(f"✅ Login SUCCESSFUL for {INSTA_USERNAME}!")
        # info = poster.client.user_info(poster.client.user_id) # CAUSES CRASH on pinned_channels
        print(f"User ID: {poster.client.user_id}")

        # Simulate scrolling and liking
        print("📜 Scrolling feed...")
        medias = poster.client.get_timeline_feed()
        print(f"Feed returned type: {type(medias)}")
        if isinstance(medias, dict):
             print(f"Keys: {medias.keys()}")
             # Try to find the list
             if 'items' in medias:
                 media_list = medias['items']
             elif 'feed_items' in medias:
                 media_list = medias['feed_items']
             else:
                 media_list = []
                 print("Could not find media list in dict.")
        else:
             media_list = list(medias)

        print(f"Found {len(media_list)} media items to process.")
        
        import random
        import time

        if media_list:
            print(f"First item type: {type(media_list[0])}")
            print(f"First item keys (if dict): {media_list[0].keys() if isinstance(media_list[0], dict) else 'Not a dict'}")

        count = 0
        for item in media_list[:5]:  # Look at first 5
            if count >= 3: break
            try:
                # Handle raw dict structure
                if isinstance(item, dict):
                    # Usually nested in 'media_or_ad' -> 'media' ?
                    if 'media_or_ad' in item:
                        media = item['media_or_ad']
                    elif 'media' in item:
                        media = item['media']
                    else:
                        media = item # Try direct
                    
                    # Get PK
                    if 'pk' in media:
                        pk = media['pk']
                    elif 'id' in media:
                        pk = media['id']
                    else:
                        print("   Skipping item without pk/id")
                        continue
                else:
                    # Object
                    pk = item.pk

                print(f"❤️ Liking media {pk}...")
                poster.client.media_like(pk)
                print(f"   Liked!")
                count += 1
                time.sleep(random.uniform(2, 5))
            except Exception as e:
                print(f"   Failed to like: {e}")
        
        print(f"✅ Finished. Liked {count} posts.")

    else:
        print("❌ Login FAILED!")
        sys.exit(1)
    
except Exception as e:
    print(f"❌ Exception during test: {e}")
    sys.exit(1)
