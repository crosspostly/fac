# -*- coding: utf-8 -*-
import os
import subprocess
import json
import datetime

# --- НАСТРОЙКИ ---
YOUTUBE_CHANNEL_URL = "https://www.youtube.com/channel/UC8hbIF2zfPI5KwlZ2Zq5RmQ/videos"
VENV_PYTHON = "./venv/bin/python3"
RUTUBE_SCRIPT = "rutube/auth_playwright.py"
BATCH_SIZE = 20
HOURS_STEP = 3

def log(msg):
    print(f"[{datetime.datetime.now()}] [BATCH] {msg}")

def get_20_youtube_videos():
    log(f"Парсим 20 видео с YouTube: {YOUTUBE_CHANNEL_URL}")
    cmd = [
        "yt-dlp",
        "--get-id",
        "--get-title",
        "--flat-playlist",
        "--playlist-end", str(BATCH_SIZE),
        YOUTUBE_CHANNEL_URL
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split("\n")
        videos = []
        for i in range(0, len(lines), 2):
            if i+1 < len(lines):
                videos.append({"title": lines[i], "id": lines[i+1]})
        return videos
    except Exception as e:
        log(f"❌ Ошибка парсинга: {e}")
        return []

def run_test():
    videos = get_20_youtube_videos()
    if not videos:
        return

    log(f"Найдено {len(videos)} видео. Начинаем массовую загрузку в очередь...")

    for index, video in enumerate(videos):
        delay = index * HOURS_STEP
        log(f"[{index+1}/{len(videos)}] Обработка: {video['title']}")
        log(f"⏱ Планируемая задержка: +{delay} ч.")

        # 1. СКАЧИВАЕМ
        video_url = f"https://www.youtube.com/watch?v={video['id']}"
        video_path = os.path.join("rutube", "test_video.mp4")
        
        # Скачиваем маленькое качество для теста, чтобы было быстрее
        dl_cmd = ["yt-dlp", "-f", "worst[ext=mp4]", "-o", video_path, video_url]
        try:
            log(f"📥 Скачиваем видео...")
            subprocess.run(dl_cmd, check=True)
            
            # 2. МЕТАДАННЫЕ
            with open("rutube/video_meta.json", "w") as f:
                json.dump({"title": video['title']}, f)

            # 3. ЗАПУСКАЕМ ПЛЕЙРАЙТ С ЗАДЕРЖКОЙ
            log(f"📤 Загружаем на RuTube с delay={delay}...")
            # Важно: запускаем через xvfb-run
            res = subprocess.run([
                "xvfb-run", VENV_PYTHON, RUTUBE_SCRIPT, 
                "--delay-hours", str(delay)
            ], capture_output=True, text=True)
            
            if res.returncode == 0:
                log(f"✅ Успешно добавлено в очередь!")
            else:
                log(f"❌ Ошибка загрузки: {res.stderr}")

        except Exception as e:
            log(f"❌ Ошибка на видео {video['id']}: {e}")
        
        # В тестовом режиме можно прервать после 1-2 видео, если нужно
        # break 

if __name__ == "__main__":
    run_test()
