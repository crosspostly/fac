# -*- coding: utf-8 -*-
import os
import requests
import subprocess
import sys
import time
import json
import datetime
import config

LOGIN = config.RUTUBE_LOGIN
PASSWORD = config.RUTUBE_PASSWORD
BASE_URL = "https://rutube.ru"
YOUTUBE_CHANNEL_URL = config.YOUTUBE_CHANNEL_URL
YT_DLP_PATH = config.YT_DLP_PATH
COOKIES_FILE = config.YOUTUBE_COOKIES_FILE

class RutubeDirectPublicTester:
    def __init__(self):
        self.log("Авторизация...")
        r = requests.post(f"{BASE_URL}/api/accounts/token_auth/", data={'username': LOGIN, 'password': PASSWORD})
        self.token = r.json().get('token')

    def log(self, msg):
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

    def get_direct_youtube_url(self):
        self.log("Получаем прямую ссылку googlevideo...")
        # Сначала получаем ID последнего видео
        cmd_id = [YT_DLP_PATH, "--cookies", COOKIES_FILE, "--get-id", "--flat-playlist", "--playlist-end", "1", YOUTUBE_CHANNEL_URL]
        res_id = subprocess.run(cmd_id, capture_output=True, text=True)
        if res_id.returncode != 0: return None, None
        
        video_id = res_id.stdout.strip()
        
        # Теперь получаем URL
        cmd_url = [YT_DLP_PATH, "--cookies", COOKIES_FILE, "-g", "-f", "best[ext=mp4]/best", f"https://youtube.com/watch?v={video_id}"]
        res_url = subprocess.run(cmd_url, capture_output=True, text=True)
        
        if res_url.returncode == 0:
            return res_url.stdout.strip(), f"YouTube Video {video_id}"
        return None, None

    def run(self):
        url, title = self.get_direct_youtube_url()
        if not url:
            self.log("❌ Не удалось получить прямой URL")
            return

        self.log(f"🚀 Загрузка на Rutube ПУБЛИЧНО...")
        headers = {"Authorization": f"Token {self.token}", "Content-Type": "application/json"}
        payload = {
            "url": url,
            "title": f"[DIRECT-PUBLIC] {title}",
            "category_id": 13,
            "is_hidden": False,
            "description": "Тест прямой загрузки YouTube -> Rutube (Public)"
        }
        
        r = requests.post(f"{BASE_URL}/api/video/", json=payload, headers=headers)
        if r.status_code in [200, 201]:
            video_id = r.json().get('video_id') or r.json().get('id')
            self.log(f"✅ Принято! ID: {video_id}")
            self.log(f"🔗 https://rutube.ru/video/{video_id}/")
            
            self.log("⏳ Ожидание статуса...")
            for i in range(20):
                time.sleep(10)
                rs = requests.get(f"{BASE_URL}/api/video/{video_id}/", headers=headers)
                data = rs.json()
                if data.get('is_deleted'):
                    self.log(f"❌ Удалено: {data.get('action_reason', {}).get('name')}")
                    return
                if data.get('duration'):
                    self.log(f"✅ УСПЕХ! Видео публично и обработано. Длительность: {data.get('duration')}")
                    return
                self.log(f"Обработка... (is_deleted: {data.get('is_deleted')})")
        else:
            self.log(f"❌ Ошибка API: {r.text}")

if __name__ == "__main__":
    RutubeDirectPublicTester().run()
