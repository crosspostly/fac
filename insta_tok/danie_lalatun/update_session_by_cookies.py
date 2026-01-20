import json
import os
from instagrapi import Client

def update_session():
    USERNAME = "danie_lalatun"
    SESSION_FILE = f"session_{USERNAME}.json"
    COOKIES_FILE = "cookies_raw.json"

    if not os.path.exists(COOKIES_FILE):
        print("Файл cookies_raw.json не найден!")
        return

    with open(COOKIES_FILE, "r") as f:
        browser_cookies = json.load(f)

    # Достаем sessionid
    sessionid = next((c['value'] for c in browser_cookies if c['name'] == 'sessionid'), None)
    
    if not sessionid:
        print("sessionid не найден!")
        return

    # Настраиваем клиент под конкретное устройство, чтобы не генерировать рандом каждый раз
    cl = Client()
    cl.set_device({
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
    # Устанавливаем фиксированный UUId на основе имени пользователя, чтобы он был постоянным
    cl.set_user_agent("Instagram 269.0.0.18.75 Android (29/10; 420dpi; 1080x1920; OnePlus; ONEPLUS A6013; OnePlus6T; qcom; en_US; 314665256)")

    try:
        print(f"Попытка входа через sessionid...")
        cl.login_by_sessionid(sessionid)
        
        # Сохраняем настройки сразу после входа
        cl.dump_settings(SESSION_FILE)
        print(f"Новая сессия сохранена в {SESSION_FILE}")

        try:
            user_info = cl.user_info_by_username(USERNAME)
            print(f"Успех! Авторизован как: {user_info.full_name} (@{user_info.username})")
        except Exception as e:
            print(f"Предупреждение: Не удалось получить инфо пользователя (это не критично): {e}")
        
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    update_session()
