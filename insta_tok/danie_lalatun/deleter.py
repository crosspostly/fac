
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from instagram_poster import InstagramPoster

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

def delete_post(media_id: str):
    """Deletes an Instagram post by its media ID."""
    load_dotenv()

    username = os.getenv("INSTAGRAM_USERNAME_DANIE_LALATUN")
    password = os.getenv("INSTAGRAM_PASSWORD_DANIE_LALATUN")

    if not username or not password:
        logger.error("Environment variables for username and password not set in .env file.")
        sys.exit(1)

    session_file_name = f"session_{username}.json"
    poster = InstagramPoster(username, password, session_file=session_file_name)

    if not poster.login():
        logger.error("Failed to login to Instagram.")
        sys.exit(1)

    try:
        if poster.client.media_delete(media_id):
            logger.info(f"Successfully deleted post with media ID: {media_id}")
        else:
            logger.error(f"Failed to delete post with media ID: {media_id}")
    except Exception as e:
        logger.error(f"An error occurred while deleting the post: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("Usage: python delete_instagram_post.py <media_id>")
        sys.exit(1)
    
    media_id_to_delete = sys.argv[1]
    delete_post(media_id_to_delete)
