# -*- coding: utf-8 -*-
import requests
import datetime

# --- НАСТРОЙКИ NO-IP ---
HOSTNAME = "crosspostly.hopto.org"
EMAIL = "ВАШ_EMAIL"
PASSWORD = "ВАШ_ПАРОЛЬ"

def log(msg):
    print(f"[{datetime.datetime.now()}] {msg}")

def update_dns():
    log(f"🔄 Checking DNS update for {HOSTNAME}...")
    
    # API No-IP для обновления
    url = f"https://dynupdate.no-ip.com/nic/update?hostname={HOSTNAME}"
    
    try:
        # Авторизация и запрос
        response = requests.get(url, auth=(EMAIL, PASSWORD), headers={"User-Agent": "Python DDNS Updater/1.0"})
        
        if "nochg" in response.text:
            log(f"✅ IP is already up to date. (Result: {response.text.strip()})")
        elif "good" in response.text:
            log(f"🚀 IP successfully updated! (Result: {response.text.strip()})")
        else:
            log(f"⚠️ Unexpected response: {response.text.strip()}")
            
    except Exception as e:
        log(f"❌ Error during DNS update: {e}")

if __name__ == "__main__":
    if EMAIL == "ВАШ_EMAIL":
        print("❌ Пожалуйста, отредактируйте файл update_dns.py и введите свои EMAIL и PASSWORD.")
    else:
        update_dns()
