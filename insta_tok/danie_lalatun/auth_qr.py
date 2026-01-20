import time
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def main():
    print("TikTok QR Code Authentication")
    print("=============================")
    
    # Setup Chrome options
    options = Options()
    if sys.platform.startswith('linux'):
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
    
    print("[INFO] Starting browser...")
    driver = webdriver.Chrome(options=options)
    
    try:
        # Navigate to login page
        print("[INFO] Navigating to TikTok login page...")
        driver.get("https://www.tiktok.com/login/phone-or-email/email")
        time.sleep(2)
        
        # Click on the link to go to QR code login if needed, or just go to /login
        driver.get("https://www.tiktok.com/login")
        
        print("[INFO] Waiting for QR code to load...")
        time.sleep(5)
        
        # Take screenshot of the page (hopefully showing QR code)
        driver.save_screenshot("login_page_qr.png")
        print(f"[SUCCESS] Screenshot saved to: {os.path.abspath('login_page_qr.png')}")
        print("[ACTION] Please download/view this image and scan the QR code with your TikTok app.")
        
        # Wait for login
        print("[INFO] Waiting for you to scan the QR code and log in...")
        print("[INFO] Checking status every 5 seconds (Timeout: 120s)")
        
        logged_in = False
        start_time = time.time()
        timeout = 120
        
        while time.time() - start_time < timeout:
            if "login" not in driver.current_url:
                print("[SUCCESS] Detected URL change (no longer on login page)!")
                logged_in = True
                break
                
            try:
                driver.find_element(By.CSS_SELECTOR, "[data-e2e='profile-icon']")
                print("[SUCCESS] Profile icon detected!")
                logged_in = True
                break
            except:
                pass
            
            time.sleep(5)
            
        if logged_in:
            print("[INFO] Login successful! Saving cookies...")
            time.sleep(3)
            
            cookies = driver.get_cookies()
            
            with open("tiktok_cookies.txt", "w", encoding="utf-8") as f:
                f.write("# Netscape HTTP Cookie File\n")
                f.write("# This is a generated file! Do not edit.\n\n")
                
                for cookie in cookies:
                    domain = cookie.get('domain', '')
                    expiration = int(cookie.get('expiry', 0)) if cookie.get('expiry') else 0
                    path = cookie.get('path', '/')
                    secure = "TRUE" if cookie.get('secure') else "FALSE"
                    name = cookie.get('name', '')
                    value = cookie.get('value', '')
                    flag = "TRUE" if domain.startswith('.') else "FALSE"
                    
                    f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expiration}\t{name}\t{value}\n")
            
            print(f"[SUCCESS] Cookies saved to: {os.path.abspath('tiktok_cookies.txt')}")
            
        else:
            print("[ERROR] Timeout waiting for login.")
            driver.save_screenshot("login_timeout.png")

    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
