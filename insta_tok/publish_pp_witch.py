#!/usr/bin/env python3
import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Настройка путей
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir)) # Чтобы видеть insta_tok как пакет
from insta_tok.instagram_poster_lib import InstagramPoster

# Загружаем переменные окружения
load_dotenv(os.path.join(current_dir, ".env"))

# Конфигурация для pp_witch
USERNAME = "pp_witch"
PASSWORD = os.getenv("INSTA_PASSWORD")
SESSION_FILE = os.path.join(current_dir, "pp_witch_session.json")
POSTED_LOG_FILE = os.path.join(current_dir, "pp_witch_posted.json")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(current_dir, "pp_witch_poster.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
            "last_update": str(import_datetime().now())
        }, f, indent=4)

def import_datetime():
    from datetime import datetime
    return datetime

def main():
    if len(sys.argv) < 2:
        print("Usage: python publish_pp_witch.py <video_path> [caption]")
        sys.exit(1)

    video_path = sys.argv[1]
    caption = sys.argv[2] if len(sys.argv) > 2 else "Video from #pp_witch #ai #art"

    if not os.path.exists(video_path):
        logger.error(f"Файл не найден: {video_path}")
        sys.exit(1)

    # Проверка на дубликаты
    posted_files = load_posted_files()
    if str(video_path) in posted_files:
        logger.warning(f"Файл уже был опубликован ранее: {video_path}")
        # Можно раскомментировать, если хотим запретить повтор
        # sys.exit(0) 

    logger.info(f"Начинаю публикацию видео: {video_path}")
    
    poster = InstagramPoster(USERNAME, PASSWORD, SESSION_FILE)
    
    if poster.login():
        logger.info("Авторизация успешна. Загружаю видео...")
        try:
            # Для видео лучше использовать upload_video
            # Но если это Reels, то upload_clip (если библиотека поддерживает)
            # instagrapi: video_upload загружает как пост, clip_upload как Reels
            
            # Попробуем clip_upload (Reels), так как это тренд
            try:
                media = poster.client.clip_upload(Path(video_path), caption)
                logger.info(f"✅ Успешно опубликовано как Reels! PK: {media.pk}")
            except AttributeError:
                # Fallback если старая версия библиотеки
                media = poster.client.video_upload(Path(video_path), caption)
                logger.info(f"✅ Успешно опубликовано как Video! PK: {media.pk}")
            
            save_posted_file(video_path)
            
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке: {e}")
            if "wait a few minutes" in str(e).lower():
                logger.warning("🕒 Инстаграм просит подождать. Попробуйте через 30-60 минут.")
            sys.exit(1)
    else:
        logger.error("❌ Не удалось авторизоваться.")
        sys.exit(1)

if __name__ == "__main__":
    main()
