import json
import time
from playwright.sync_api import sync_playwright

# Загружаем сессию
with open("insta_tok/pp_witch_session.json", "r") as f:
    session_data = json.load(f)

# Формируем куки для Playwright
cookies = []
for name, value in session_data.get("cookies", {}).items():
    cookies.append({
        "name": name,
        "value": value,
        "domain": ".instagram.com",
        "path": "/",
        "secure": True,
        "sameSite": "None" # Важно для Playwright
    })

def run():
    print("🚀 Запускаю визуальную проверку в реальном времени...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="en-US"
        )
        
        context.add_cookies(cookies)
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            print("🌍 Переход на главную Instagram...")
            page.goto("https://www.instagram.com/", wait_until="networkidle", timeout=30000)
            
            time.sleep(5)
            print(f"📄 Заголовок страницы: {page.title()}")
            print(f"🔗 URL: {page.url}")

            # Проверяем наличие типичных элементов
            body_text = page.inner_text("body")
            
            print("\n" + "="*20 + " ТЕКСТ НА ЭКРАНЕ " + "="*20)
            # Убираем пустые строки для компактности
            clean_text = '\n'.join([line.strip() for line in body_text.splitlines() if line.strip()])
            print(clean_text[:1000]) 
            print("="*20 + " КОНЕЦ ТЕКСТА " + "="*20 + "\n")

            if "challenge" in page.url or "suspicious" in body_text.lower():
                print("⚠️⚠️⚠️ ОБНАРУЖЕНА КАПЧА ИЛИ ПРОВЕРКА! ⚠️⚠️⚠️")
            elif "login" in page.url:
                print("❌ Выбросило на страницу входа (куки не сработали?)")
            else:
                print("✅ Похоже на успешный вход (лента).")

            page.screenshot(path="debug_live_now.png")
            print("📸 Скриншот сохранен как debug_live_now.png")

        except Exception as e:
            print(f"❌ Ошибка: {e}")
            page.screenshot(path="debug_error_live.png")
        
        browser.close()

if __name__ == "__main__":
    run()
