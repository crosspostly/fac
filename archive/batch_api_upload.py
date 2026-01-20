# -*- coding: utf-8 -*-
import requests
import json
import subprocess
import datetime
import time
import os

# --- НАСТРОЙКИ ---
LOGIN = 'nlpkem@ya.ru'
PASSWORD = '*V8u2p2r'
YOUTUBE_CHANNEL_URL = "https://www.youtube.com/channel/UC8hbIF2zfPI5KwlZ2Zq5RmQ/videos"
BASE_URL = "https://rutube.ru"
BATCH_SIZE = 20

def log(msg):
    print(f"[{datetime.datetime.now()}] {msg}")

def get_token():
    """Получаем API токен"""
    url = f"{BASE_URL}/api/accounts/token_auth/"
    try:
        r = requests.post(url, data={'username': LOGIN, 'password': PASSWORD})
        if r.status_code == 200:
            return r.json().get('token')
    except Exception as e:
        log(f"Ошибка получения токена: {e}")
    return None

def get_youtube_videos(limit=20):
    """Парсим видео с YouTube через yt-dlp"""
    log(f"Парсим {limit} видео с канала...")
    yt_dlp_path = "./yt-dlp" # Используем локальный yt-dlp
    cmd = [
        yt_dlp_path,
        "--get-id",
        "--get-title",
        "--flat-playlist",
        "--playlist-end", str(limit),
        YOUTUBE_CHANNEL_URL
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split("\n")
        videos = []
        for i in range(0, len(lines), 2):
            if i+1 < len(lines):
                videos.append({
                    "title": lines[i],
                    "url": f"https://www.youtube.com/watch?v={lines[i+1]}"
                })
        return videos
    except Exception as e:
        log(f"Ошибка парсинга YouTube: {e}")
        return []

def get_direct_url(video_url):
    """Получаем прямую ссылку на файл через yt-dlp"""
    cmd = ["./yt-dlp", "-g", "-f", "best[ext=mp4]/best", video_url]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        log(f"Ошибка получения прямой ссылки для {video_url}: {e}")
        return None

def start_batch():
    token = get_token()
    if not token:
        log("❌ Не удалось авторизоваться.")
        return

    videos = get_youtube_videos(BATCH_SIZE)
    if not videos:
        log("❌ Видео не найдены.")
        return

    log(f"✅ Найдено {len(videos)} видео. Начинаем импорт...")

    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }

    for i, video in enumerate(videos):
        log(f"[{i+1}/{len(videos)}] Обрабатываем: {video['title']}")
        
        # Получаем прямую ссылку
        direct_url = get_direct_url(video['url'])
        if not direct_url:
            log(f"⚠️ Пропускаем (не удалось получить ссылку)")
            continue
            
        payload = {
            "url": direct_url,
            "title": video['title'],
            "description": "Перенесено с YouTube канала ЦУП Кулинария",
            "category_id": 13, # Хобби/Еда
            "is_hidden": False # Сразу публичные
        }

        try:
            # Используем /api/video/ для импорта по ссылке
            r = requests.post(f"{BASE_URL}/api/video/", json=payload, headers=headers)
            
            if r.status_code in [200, 201]:
                data = r.json()
                log(f"✅ Успешно! ID: {data.get('video_id')}")
            else:
                log(f"❌ Ошибка: {r.status_code} - {r.text}")
            
            # Небольшая пауза между запросами, чтобы не забанили
            time.sleep(2)
            
        except Exception as e:
            log(f"❌ Критическая ошибка на видео {i}: {e}")

if __name__ == "__main__":
    start_batch()
