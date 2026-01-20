#!/usr/bin/env python3
import os
import sys
import json
import logging
from pathlib import Path

# Добавляем путь для импортов
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))

# Настройка путей
COOKIES_FILE = os.path.join(current_dir, "tiktok_cookies.txt")
POSTED_LOG_FILE = os.path.join(current_dir, "tiktok_posted.json")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(current_dir, "tiktok_poster.log")),
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
    from datetime import datetime
    posted = load_posted_files()
    posted.add(str(filename))
    with open(POSTED_LOG_FILE, 'w') as f:
        json.dump({
            "posted_files": list(posted),
            "last_update": str(datetime.now())
        }, f, indent=4)

def main():
    if len(sys.argv) < 2:
        print("Usage: python publish_tiktok.py <video_path> [caption]")
        sys.exit(1)

    video_path = sys.argv[1]
    caption = sys.argv[2] if len(sys.argv) > 2 else "New video #fyp #trending"

    if not os.path.exists(video_path):
        logger.error(f"Файл не найден: {video_path}")
        sys.exit(1)

    # Проверка на дубликаты
    posted_files = load_posted_files()
    if str(video_path) in posted_files:
        logger.warning(f"Файл уже был опубликован в TikTok ранее: {video_path}")
        # sys.exit(0)

    logger.info(f"🚀 Начинаю публикацию в TikTok: {video_path}")
    
    try:
        from tiktok_uploader.upload import upload_video
        
        # Загрузка через tiktok-uploader
        # Headless=True для работы на сервере
        # Описание (description) в ТикТоке - это caption
        success = upload_video(
            video_path,
            description=caption,
            cookies=COOKIES_FILE,
            headless=True
        )
        
        if not success: # Библиотека возвращает список неудачных загрузок (пустой список = успех)
            logger.info(f"✅ Видео успешно опубликовано в TikTok!")
            save_posted_file(video_path)
        else:
            logger.error(f"❌ Ошибка при публикации: {success}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка TikTok: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
