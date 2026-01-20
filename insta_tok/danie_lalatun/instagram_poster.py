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
        
        # Фиксируем устройство, чтобы не генерировать новые ID при каждом перелогине
        self.client.set_device({
            "app_version": "269.0.0.18.75",
            "android_version": 29,
            "android_release": "10",
            "dpi": "420dpi",
            "resolution": "1080x1920",
            "manufacturer": "OnePlus",
            "device": "OnePlus6T",
            "model": "ONEPLUS A6013",
            "cpu": "qcom",
            "version_code": "314665256"
        })
        self.client.set_user_agent("Instagram 269.0.0.18.75 Android (29/10; 420dpi; 1080x1920; OnePlus; ONEPLUS A6013; OnePlus6T; qcom; en_US; 314665256)")
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
