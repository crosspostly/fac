# -*- coding: utf-8 -*-
import os

# --- RUTUBE CREDENTIALS ---
RUTUBE_LOGIN = 'nlpkem@ya.ru'
RUTUBE_PASSWORD = '*V8u2p2r'

# --- YOUTUBE SETTINGS ---
# Канал-источник
YOUTUBE_CHANNEL_URL = "https://www.youtube.com/channel/UC8hbIF2zfPI5KwlZ2Zq5RmQ"

# --- LOCAL SERVER SETTINGS ---
# Внешний IP вашего сервера (для того, чтобы Rutube мог скачивать файлы)
# ВАЖНО: Используйте здесь ДОМЕННОЕ ИМЯ, а не IP-адрес. Rutube требует домен для корректной работы колбэков.
# Например: "my-cool-domain.com"
PUBLIC_IP = "crosspostly.hopto.org"
SERVER_PORT = 5005

# --- PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
DB_FILE = os.path.join(BASE_DIR, "sync_db.sqlite")

# Cookies
YOUTUBE_COOKIES_FILE = os.path.join(BASE_DIR, "youtube_cookies.txt") # Для yt-dlp
RUTUBE_COOKIES_FILE = os.path.join(BASE_DIR, "rutube_cookies.json")  # Для Playwright

# Tools
YT_DLP_PATH = os.path.join(BASE_DIR, "yt-dlp")
