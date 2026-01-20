import os
import sys
from tiktok_uploader.upload import upload_video

# Путь к кукам
COOKIES = "insta_tok/tiktok_cookies.txt"

print(f"🔍 Проверка куков ТикТока из {COOKIES}...")

# Библиотека не имеет явного метода 'check_login',
# но мы можем попробовать инициировать пустую сессию или просто проверить файл
if os.path.exists(COOKIES):
    with open(COOKIES, 'r') as f:
        content = f.read()
        if "sessionid" in content:
            print("✅ В куках найден sessionid.")
        else:
            print("⚠️ Внимание: sessionid не найден в файле куков!")
else:
    print("❌ Файл куков не создан!")

# Попробуем запустить тестовый скрипт, который проверит валидность куков через селениум
# (просто откроет страницу профиля и проверит залогинены ли мы)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

def check_tiktok_login():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Пытаемся найти chromedriver
    service = Service(executable_path="/usr/bin/chromedriver")
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.get("https://www.tiktok.com/")
        
        # Загружаем куки из файла Netscape
        print("📥 Загрузка куков в браузер...")
        with open(COOKIES, 'r') as f:
            for line in f:
                if not line.startswith('#') and line.strip():
                    parts = line.strip().split('\t')
                    if len(parts) >= 7:
                        cookie = {
                            'domain': parts[0],
                            'name': parts[5],
                            'value': parts[6],
                            'path': parts[2],
                            'secure': parts[3] == 'TRUE'
                        }
                        try:
                            driver.add_cookie(cookie)
                        except:
                            pass
        
        driver.refresh()
        import time
        time.sleep(5)
        
        print(f"📄 Заголовок страницы: {driver.title}")
        if "Login" in driver.title or "Войти" in driver.title:
            print("❌ Куки НЕ СРАБОТАЛИ (видим страницу входа).")
        else:
            print("✅ Похоже, мы авторизованы!")
            
        driver.quit()
    except Exception as e:
        print(f"❌ Ошибка при проверке через браузер: {e}")

if __name__ == "__main__":
    check_tiktok_login()
