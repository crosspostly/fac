import json
import time
import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Загружаем пароль
load_dotenv("insta_tok/.env")
PASSWORD = os.getenv("INSTA_PASSWORD")
USERNAME = "pp_witch"

# Загружаем сессию (чтобы взять Device ID, но куки, возможно, мешают - попробуем БЕЗ них или С ними)
# Лучше попробовать с чистого листа, раз старые куки водят нас по кругу
cookies = [] 

def run():
    print("🚀 Полный вход через браузер (Логин + Пароль)...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        )
        # context.add_cookies(cookies) # НЕ добавляем старые куки, идем начисто
        page = context.new_page()

        try:
            print("🌍 Переход на Instagram Login...")
            page.goto("https://www.instagram.com/accounts/login/", wait_until="networkidle", timeout=60000)
            
            # Принимаем куки если есть
            try:
                page.click('button:has-text("Allow all cookies")', timeout=3000)
            except:
                pass

            print("⌨️ Ввожу данные...")
            page.fill('input[name="username"]', USERNAME)
            time.sleep(1)
            page.fill('input[name="password"]', PASSWORD)
            time.sleep(1)
            
            print("Bd Жму кнопку входа...")
            page.click('button[type="submit"]')
            
            print("⏳ Жду результата (15 сек)...")
            page.wait_for_timeout(15000)
            
            # Проверяем результат
            body_text = page.inner_text("body")
            print("\n" + "="*20 + " РЕЗУЛЬТАТ ВХОДА " + "="*20)
            print('\n'.join([l.strip() for l in body_text.splitlines() if l.strip()][:30]))
            print("="*20 + " КОНЕЦ " + "="*20 + "\n")
            
            # Сохраняем куки если вошли
            new_cookies = context.cookies()
            new_session_id = None
            cookie_dict = {}
            for c in new_cookies:
                cookie_dict[c['name']] = c['value']
                if c['name'] == 'sessionid':
                    new_session_id = c['value']

            if new_session_id:
                print(f"✅ УРА! ПОЛУЧЕН НОВЫЙ SESSION ID: {new_session_id[:20]}...")
                
                # Ищем ID пользователя в куках ds_user_id
                ds_user_id = cookie_dict.get("ds_user_id", "69564892126") # Фолбек на известный ID

                final_settings = {
                    "authorization_data": {
                        "ds_user_id": ds_user_id,
                        "sessionid": new_session_id
                    },
                    "cookies": cookie_dict,
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                    "device_settings": {
                        "app_version": "269.0.0.18.75",
                        "android_version": 29, 
                        "android_release": "10", 
                        "manufacturer": "OnePlus",
                        "device": "OnePlus6T",
                        "model": "ONEPLUS A6013"
                    }
                }
                
                with open("insta_tok/pp_witch_session.json", "w") as f:
                    json.dump(final_settings, f, indent=4)
                print("💾 Новая сессия сохранена!")
            else:
                print("❌ SessionID не получен. Вход не удался (см. текст выше).")
                page.screenshot(path="debug_login_fail.png")

        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        browser.close()

if __name__ == "__main__":
    run()