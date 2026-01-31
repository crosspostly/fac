import config
import subprocess
import json
import os
import atexit

TEMP_COOKIE_FILE = "youtube_cookies_debug.txt"

def cleanup():
    if os.path.exists(TEMP_COOKIE_FILE):
        os.remove(TEMP_COOKIE_FILE)

atexit.register(cleanup)

env_cookies = os.environ.get("YOUTUBE_COOKIES_TXT")
cookie_arg = []

if env_cookies:
    with open(TEMP_COOKIE_FILE, "w") as f:
        f.write(env_cookies)
    cookie_arg = ["--cookies", TEMP_COOKIE_FILE]
    print("🍪 Используем куки из YOUTUBE_COOKIES_TXT")
elif os.path.exists("youtube_cookies.txt") and os.path.getsize("youtube_cookies.txt") > 0:
    cookie_arg = ["--cookies", "youtube_cookies.txt"]
    print("🍪 Используем локальный youtube_cookies.txt")

print(f"URL канала: {config.YOUTUBE_CHANNEL_URL}")
print(f"Путь к yt-dlp: {config.YT_DLP_PATH}")

cmd = [config.YT_DLP_PATH, "--dump-json", "--flat-playlist", "--playlist-end", "3"] + cookie_arg + [config.YOUTUBE_CHANNEL_URL]
print(f"Запускаем команду: {' '.join(cmd)}")

try:
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"❌ Ошибка yt-dlp (код {res.returncode}):")
        print(res.stderr)
    else:
        print("✅ yt-dlp успешно отработал!")
        videos = []
        for line in res.stdout.strip().split("\n"):
            if line:
                try:
                    v = json.loads(line)
                    print(f" - Найдено видео: {v.get('title')} (ID: {v.get('id')})")
                except:
                    pass
        if not videos:
            print("⚠️ Список видео пуст.")
except Exception as e:
    print(f"❌ Исключение: {e}")
