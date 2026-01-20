# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import requests
import subprocess
import config
import re

# --- КОНФИГУРАЦИЯ ---
VIDEO_FILE_NAME = "test_video.mp4"
VIDEO_FILE_PATH = os.path.join(os.path.dirname(__file__), VIDEO_FILE_NAME)
VIDEO_TITLE = f"Надежная проверка загрузки {time.strftime('%H:%M:%S')}"

# --- УТИЛИТЫ ---
def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def ensure_server_running():
    """Проверяет, запущен ли локальный сервер, и если нет - запускает его."""
    try:
        requests.get(f"http://localhost:{config.SERVER_PORT}/health", timeout=2)
        log("✅ Локальный сервер уже запущен.")
        return True
    except requests.exceptions.ConnectionError:
        log("🔌 Локальный сервер не отвечает. Запускаем...")
        server_script = os.path.join(os.path.dirname(__file__), "server_simple.py")
        try:
            subprocess.Popen(
                [sys.executable, server_script],
                stdout=open('server_simple.log', 'w'),
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
            time.sleep(3) # Даем время на запуск
            log("✅ Сервер запущен в фоновом режиме. Логи в server_simple.log")
            return True
        except Exception as e:
            log(f"❌ Не удалось запустить сервер: {e}")
            return False

def get_rutube_token():
    """Получает токен авторизации Rutube."""
    log("🔑 Получение токена авторизации...")
    try:
        response = requests.post(
            "https://rutube.ru/api/accounts/token_auth/",
            data={'username': config.RUTUBE_LOGIN, 'password': config.RUTUBE_PASSWORD}
        )
        response.raise_for_status()
        token = response.json().get('token')
        if token:
            log("✅ Токен успешно получен.")
            return token
        else:
            log("❌ Токен не найден в ответе сервера.")
            return None
    except requests.exceptions.RequestException as e:
        log(f"❌ Ошибка авторизации: {e}")
        return None

def generate_hashtags(title):
    """Генерирует хештеги из заголовка."""
    words = re.findall(r'\b\w+\b', title.lower())
    hashtags = list(set(word for word in words if len(word) > 3))
    return hashtags[:5] # Ограничим до 5 хештегов

# --- ОСНОВНОЙ СКРИПТ ---
def main():
    log("🚀 Старт процесса загрузки и верификации.")

    # 1. Проверить наличие видеофайла
    if not os.path.exists(VIDEO_FILE_PATH):
        log(f"❌ Видеофайл не найден: {VIDEO_FILE_PATH}")
        return

    # 2. Запустить сервер
    if not ensure_server_running():
        return

    # 3. Получить токен
    token = get_rutube_token()
    if not token:
        return

    # 4. Сформировать URL и payload
    video_url = f"http://{config.PUBLIC_IP}:{config.SERVER_PORT}/static/{VIDEO_FILE_NAME}"
    hashtags = generate_hashtags(VIDEO_TITLE)
    
    payload = {
        "url": video_url,
        "title": VIDEO_TITLE,
        "description": "Это видео загружено через локальный сервер с последующей верификацией статуса.",
        "category_id": 13, # Разное
        "is_hidden": False,
        "hashtags": hashtags,
        "callback_url": f"http://{config.PUBLIC_IP}:{config.SERVER_PORT}/webhook?file={VIDEO_FILE_NAME}"
    }
    
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }

    # 5. Отправить запрос на загрузку
    log(f"📤 Отправка запроса на загрузку видео. Источник: {video_url}")
    log(f"📋 Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post("https://rutube.ru/api/video/", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        video_id = data.get('video_id') or data.get('id')
        if not video_id:
            log(f"❌ API не вернуло ID видео. Ответ: {data}")
            return
        log(f"✅ Запрос принят Rutube. ID видео: {video_id}")

    except requests.exceptions.RequestException as e:
        log(f"❌ Ошибка API при отправке запроса: {e}")
        if e.response:
            log(f"Ответ сервера: {e.response.text}")
        return

    # 6. Мониторинг статуса
    log(f"🕵️‍♂️ Запуск мониторинга статуса для видео ID: {video_id}")
    max_wait_time = 900  # 15 минут
    check_interval = 15  # 15 секунд
    start_time = time.time()

    while time.time() - start_time < max_wait_time:
        try:
            check_url = f"https://rutube.ru/api/video/{video_id}/"
            res_check = requests.get(check_url, headers={"Authorization": f"Token {token}"})
            
            if res_check.status_code != 200:
                log(f"⚠️ Не удалось получить статус (код {res_check.status_code}). Повтор через {check_interval} сек.")
                time.sleep(check_interval)
                continue

            status_data = res_check.json()
            status = status_data.get('status')
            is_deleted = status_data.get('is_deleted')
            reason = status_data.get('action_reason', {}).get('name', 'N/A')

            log(f"⏳ Статус: [status: {status}], [is_deleted: {is_deleted}], [reason: {reason}]")

            if status == 'ready':
                log("🎉🎉🎉 УСПЕХ! Видео обработано и готово к просмотру.")
                log(f"🔗 Ссылка: {status_data.get('video_url')}")
                return

        except requests.exceptions.RequestException as e:
            log(f"⚠️ Ошибка сети при проверке статуса: {e}")

        time.sleep(check_interval)

    log("⏰ ВРЕМЯ ОЖИДАНИЯ ИСТЕКЛО. Видео не было обработано за 15 минут.")

if __name__ == "__main__":
    main()
