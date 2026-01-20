import logging
import os
import sys
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.exceptions import (
    BadPassword, ReloginAttemptExceeded, ChallengeRequired,
    SelectContactPointRecoveryForm, RecaptchaChallengeForm,
    FeedbackRequired, PleaseWaitFewMinutes, LoginRequired
)

# Настройка глубокого логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("DebugInsta")

def debug_login():
    load_dotenv()
    
    username = os.getenv("INSTAGRAM_USERNAME_DANIE_LALATUN")
    password = os.getenv("INSTAGRAM_PASSWORD_DANIE_LALATUN")

    if not username or not password:
        logger.error("Нет логина/пароля в .env")
        return

    print(f"--- НАЧАЛО ДИАГНОСТИКИ ДЛЯ {username} ---")
    
    cl = Client()
    # Эмуляция стандартного устройства
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
    
    try:
        print("Попытка входа...")
        cl.login(username, password)
        print(">>> УСПЕШНЫЙ ВХОД! <<<")
        
        info = cl.account_info()
        print(f"ID аккаунта: {info.pk}")
        
    except BadPassword:
        print("!!! ОШИБКА: Неверный пароль.")
    except ChallengeRequired:
        print("!!! ТРЕБУЕТСЯ ПОДТВЕРЖДЕНИЕ (Challenge).")
        print("Инстаграм просит код из SMS или Email.")
    except FeedbackRequired as e:
        print(f"!!! БЛОКИРОВКА ДЕЙСТВИЯ (FeedbackRequired): {e}")
        print("Обычно это значит бан по IP или Device ID.")
    except PleaseWaitFewMinutes:
        print("!!! ОШИБКА: 'Подождите несколько минут'.")
        print("Слишком много попыток входа.")
    except Exception as e:
        print(f"!!! НЕИЗВЕСТНАЯ ОШИБКА: {type(e).__name__}")
        print(f"Текст ошибки: {e}")

if __name__ == "__main__":
    debug_login()
