#!/usr/bin/env python3
import os
import sys
import logging
from pathlib import Path
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InstagramPoster:
    def __init__(self, username, password, session_file=None):
        self.username = username
        self.password = password
        self.session_file = Path(session_file) if session_file else None
        self.client = Client()
        
        # Смена устройства на Samsung S22 Ultra
        self.client.set_device({
            "app_version": "269.0.0.18.75",
            "android_version": 31,
            "android_release": "12",
            "dpi": "480dpi",
            "resolution": "1440x3088",
            "manufacturer": "samsung",
            "device": "SM-S908B",
            "model": "SM-S908B",
            "cpu": "exynos2200",
            "version_code": "314665256"
        })
        self.client.set_user_agent("Instagram 269.0.0.18.75 Android (31/12; 480dpi; 1440x3088; samsung; SM-S908B; SM-S908B; exynos2200; en_US; 314665256)")
        self.client.delay_range = [2, 5]

    def login(self):
        """
        Умная авторизация: Сессия -> Проверка -> Логин -> Сохранение
        """
        # 1. Попытка загрузить сессию
        if self.session_file and self.session_file.exists():
            try:
                logger.info(f"Загружаю сессию из {self.session_file}")
                self.client.load_settings(self.session_file)
                
                # Проверка валидности (легкий запрос)
                self.client.get_timeline_feed() 
                logger.info("Сессия валидна.")
                return True
            except (LoginRequired, Exception) as e:
                logger.warning(f"Сессия невалидна ({e}), пробую вход по паролю...")

        # 2. Вход по паролю (если сессии нет или она протухла)
        try:
            logger.info(f"Вход по паролю для {self.username}...")
            self.client.login(self.username, self.password)
            logger.info("Вход успешен.")
            
            # 3. Сохранение новой сессии
            if self.session_file:
                self.client.dump_settings(self.session_file)
                logger.info(f"Сессия сохранена в {self.session_file}")
            
            return True
        except Exception as e:
            logger.error(f"Критическая ошибка входа: {e}")
            return False

    def upload_video(self, video_path, caption):
        try:
            logger.info(f"Загрузка видео: {video_path}")
            media = self.client.video_upload(Path(video_path), caption)
            return media.dict()
        except Exception as e:
            logger.error(f"Ошибка загрузки видео: {e}")
            return None

    def upload_photo(self, photo_path, caption):
        try:
            logger.info(f"Загрузка фото: {photo_path}")
            media = self.client.photo_upload(Path(photo_path), caption)
            return media.dict()
        except Exception as e:
            logger.error(f"Ошибка загрузки фото: {e}")
            return None
