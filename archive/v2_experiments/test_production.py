# -*- coding: utf-8 -*-
import os
import requests
import subprocess
import sys
import time
import json
import datetime
import config

# --- КОНФИГУРАЦИЯ ---
LOGIN = config.RUTUBE_LOGIN
PASSWORD = config.RUTUBE_PASSWORD
BASE_URL = "https://rutube.ru"
YOUTUBE_CHANNEL_URL = config.YOUTUBE_CHANNEL_URL
COOKIES_FILE = config.YOUTUBE_COOKIES_FILE
YT_DLP_PATH = config.YT_DLP_PATH
UPLOADS_DIR = config.UPLOADS_DIR
PUBLIC_DOMAIN = config.PUBLIC_IP
SERVER_PORT = config.SERVER_PORT # 5006

LOG_FILE_MD = "experiment_log.md"

class RutubePublicTester:
    def __init__(self):
        self.token = None
        self.server_proc = None
        self.start_local_server()
        self.authenticate()

    def log(self, msg):
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

    def start_local_server(self):
        self.log(f"Запуск локального сервера на порту {SERVER_PORT}...")
        pkill = subprocess.run(["pkill", "-f", "server_simple.py"])
        
        server_script = os.path.join(os.path.dirname(__file__), "server_simple.py")
        self.server_proc = subprocess.Popen(
            [sys.executable, server_script],
            stdout=open("server_stdout.log", "w"),
            stderr=open("server_stderr.log", "w"),
            start_new_session=True
        )
        time.sleep(3)
        
        # Проверка
        try:
            r = requests.get(f"http://localhost:{SERVER_PORT}/health", timeout=2)
            if r.status_code == 200:
                self.log("✅ Локальный сервер запущен и отвечает.")
            else:
                self.log(f"⚠️ Сервер ответил {r.status_code}")
        except Exception as e:
            self.log(f"❌ Не удалось запустить сервер: {e}")

    def authenticate(self):
        self.log("Авторизация на Rutube...")
        try:
            r = requests.post(f"{BASE_URL}/api/accounts/token_auth/", data={'username': LOGIN, 'password': PASSWORD})
            if r.status_code == 200:
                self.token = r.json().get('token')
                self.log(f"✅ Успешно. Токен: {self.token[:10]}...")
            else:
                self.log(f"❌ Ошибка авторизации: {r.text}")
                sys.exit(1)
        except Exception as e:
            self.log(f"❌ Исключение при авторизации: {e}")
            sys.exit(1)

    def get_latest_youtube_video(self):
        self.log("Получаем последнее видео с YouTube...")
        cmd = [YT_DLP_PATH, "--cookies", COOKIES_FILE, "--get-id", "--get-title", "--flat-playlist", "--playlist-end", "1", YOUTUBE_CHANNEL_URL]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            lines = res.stdout.strip().split("\n")
            if len(lines) >= 2:
                self.log(f"🎬 Видео: {lines[0]} ({lines[1]})")
                return lines[1], lines[0]
        return None, None

    def upload_to_rutube(self, method_name, video_url, title):
        self.log(f"🚀 Загрузка [{method_name}] (ПУБЛИЧНО)... URL: {video_url}")
        headers = {"Authorization": f"Token {self.token}", "Content-Type": "application/json"}
        payload = {
            "url": video_url,
            "title": f"[PUBLIC-{method_name}] {title[:40]}",
            "category_id": 13,
            "is_hidden": False,
            "description": f"Тест {method_name} {datetime.datetime.now()}"
        }
        r = requests.post(f"{BASE_URL}/api/video/", json=payload, headers=headers)
        if r.status_code in [200, 201]:
            video_id = r.json().get('video_id') or r.json().get('id')
            self.log(f"✅ OK. ID: {video_id}")
            self.poll_status(video_id, method_name, video_url)
        else:
            self.log(f"❌ Ошибка API: {r.text}")

    def poll_status(self, video_id, method, url):
        headers = {"Authorization": f"Token {self.token}"}
        for i in range(24): # 2 минуты
            time.sleep(5)
            r = requests.get(f"{BASE_URL}/api/video/{video_id}/", headers=headers)
            if r.status_code == 200:
                data = r.json()
                if data.get('is_deleted'):
                    reason = data.get('action_reason', {}).get('name', 'Unknown')
                    self.log(f"❌ Удалено. Причина: {reason}")
                    self.record_result(method, url, "FAILED", reason)
                    return
                if data.get('duration'):
                    self.log(f"✅ Готово! Длительность: {data.get('duration')}")
                    self.record_result(method, url, "SUCCESS", f"Duration: {data.get('duration')}")
                    return
            if i % 6 == 0: self.log(f"Ожидание... ({i*5}s)")
        self.log("✅ Видео активно (не удалено за 2 мин).")
        self.record_result(method, url, "ALIVE", "Survied 2m")

    def record_result(self, method, url, status, details):
        line = f"| {datetime.datetime.now().isoformat()} | **{method}** | `{status}` | [Link]({url}) | {details} |\n"
        with open(LOG_FILE_MD, 'a') as f: f.write(line)

    def run(self):
        vid, title = self.get_latest_youtube_video()
        if not vid: return
        
        # Файл VUcDSzgFLnQ.mp4 уже есть
        filename = f"{vid}.mp4"
        
        # Тест STATIC
        static_url = f"https://{PUBLIC_DOMAIN}/rutube-webhook/static/{filename}"
        self.upload_to_rutube("STATIC", static_url, title)
        
        # Тест WEBHOOK
        webhook_url = f"https://{PUBLIC_DOMAIN}/rutube-webhook/webhook?file={filename}"
        self.upload_to_rutube("WEBHOOK", webhook_url, title)

if __name__ == "__main__":
    RutubePublicTester().run()
