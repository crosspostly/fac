# -*- coding: utf-8 -*-
import os
import sys
import time
from rutube_uploader import RutubeUploader
import config

def main():
    # 1. Данные из конфига
    LOGIN = config.RUTUBE_LOGIN
    PASSWORD = config.RUTUBE_PASSWORD
    
    # 2. Локальный файл
    LOCAL_FILE = os.path.join(os.path.dirname(__file__), "test_video.mp4")
    if not os.path.exists(LOCAL_FILE):
        print(f"[{time.strftime('%H:%M:%S')}] ❌ Файл {LOCAL_FILE} не найден!")
        return

    TITLE = f"Тестовая загрузка по URL {time.strftime('%H:%M:%S')}"
    DESC = "Это видео загружено через API Rutube методом передачи URL. Проверка статусов."
    
    print(f"[{time.strftime('%H:%M:%S')}] 🚀 Инициализация загрузчика для {LOGIN}...")
    
    # 3. Создаем экземпляр загрузчика
    uploader = RutubeUploader(LOGIN, PASSWORD)
    
    # 4. Запускаем загрузку
    print(f"[{time.strftime('%H:%M:%S')}] 📤 Отправка файла...")
    result = uploader.upload_local_file(
        file_path=LOCAL_FILE,
        title=TITLE,
        description=DESC,
        category_id=13
    )
    
    if result:
        video_id = result.get('video_id') or result.get('id')
        print(f"[{time.strftime('%H:%M:%S')}] ✅ API приняло запрос. ID: {video_id}")
        
        # 5. Проверяем статус
        print(f"[{time.strftime('%H:%M:%S')}] 🔎 Запускаем проверку статуса (WAIT LOOP)...")
        uploader.wait_for_status(video_id, max_retries=10, sleep_time=5)
    else:
        print(f"[{time.strftime('%H:%M:%S')}] ❌ Загрузка не удалась (API вернуло ошибку).")

if __name__ == "__main__":
    main()