from playwright.sync_api import sync_playwright
import json
import os
import time
import sys
import config

COOKIES_FILE = 'rutube_cookies.json'
UPLOAD_URL = "https://studio.rutube.ru/videos/upload"

def upload_video_playwright(file_path, title, description=""):
    print(f"[{time.strftime('%H:%M:%S')}] 🤖 Starting Playwright Browser Upload...")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Headless
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
        
        # Load cookies if available
        if os.path.exists(COOKIES_FILE):
            with open(COOKIES_FILE, 'r') as f:
                context.add_cookies(json.load(f))
        
        page = context.new_page()
        
        # 1. Go to Upload Page
        print(f"Loading {UPLOAD_URL}...")
        try:
            page.goto(UPLOAD_URL, timeout=60000)
            page.wait_for_load_state('networkidle')
        except Exception as e:
            print(f"❌ Failed to load page: {e}")
            page.screenshot(path="pw_error_load.png")
            browser.close()
            return False

        # Check if login is needed
        if "login" in page.url:
            print("⚠️ Redirected to Login. Cookies might be invalid.")
            # Here we could implement login, but let's assume cookies work for now
            page.screenshot(path="pw_login_redirect.png")
            browser.close()
            return False

        # 2. Upload File
        try:
            print("📂 Selecting file...")
            # Look for file input. It might be hidden.
            # Rutube usually has a button that triggers a hidden input.
            # We can force the input to be visible or just point to 'input[type=file]'
            
            # Start waiting for file chooser logic is brittle if input is directly available
            # Let's try direct set_input_files on the input element
            
            file_input = page.locator("input[type='file']")
            # Sometimes there are multiple, usually the first one works for the main upload
            file_input.first.set_input_files(file_path)
            print(f"✅ File set: {file_path}")
            
        except Exception as e:
            print(f"❌ File upload selector failed: {e}")
            page.screenshot(path="pw_error_file.png")
            browser.close()
            return False

        # 3. Fill Details
        try:
            print("📝 Filling details...")
            # Title
            page.wait_for_selector("input[name='title']", timeout=30000)
            page.fill("input[name='title']", title)
            
            # Description
            desc_area = page.locator("textarea[name='description']")
            if desc_area.count() > 0:
                desc_area.fill(description)
            
            # Category (Optional but good)
            # Select first if not selected?
            
        except Exception as e:
             print(f"❌ Form filling failed: {e}")
             page.screenshot(path="pw_error_form.png")
             browser.close()
             return False

        # 4. Wait for Upload Completion
        # We need to find a progress indicator or wait until "Save" is enabled.
        print("⏳ Waiting for upload/processing...")
        # Usually there's a text "Загружено 100%" or similar.
        # Or the "Save" button becomes enabled.
        
        save_btn = page.locator("button:has-text('Сохранить')").first
        if not save_btn.is_visible():
             save_btn = page.locator("button:has-text('Опубликовать')").first
        
        # Poll for button to be enabled
        max_wait = 300 # 5 minutes for upload
        uploaded = False
        for i in range(max_wait):
            if save_btn.is_enabled():
                uploaded = True
                break
            time.sleep(1)
            if i % 10 == 0: print(f"   Uploading... {i}s")
        
        if not uploaded:
            print("❌ Upload timed out.")
            page.screenshot(path="pw_timeout.png")
            browser.close()
            return False

        # 5. Click Save/Publish
        print("💾 Clicking Save/Publish...")
        save_btn.click()
        
        # Wait for confirmation/redirect
        page.wait_for_timeout(5000)
        page.screenshot(path="pw_success.png")
        print("✅ Upload flow completed.")
        
        browser.close()
        return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Path to video file")
    parser.add_argument("--title", help="Video title", default="Test Video Playwright")
    args = parser.parse_args()
    
    upload_video_playwright(args.file, args.title)
