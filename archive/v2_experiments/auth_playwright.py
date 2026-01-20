import json
import time
import os
import datetime
import sys
from playwright.sync_api import sync_playwright

# Credentials
COOKIES_FILE = os.path.join(os.path.dirname(__file__), "rutube_cookies.json")
VIDEO_FILE = os.path.join(os.path.dirname(__file__), "test_video.mp4")

def log(msg):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")

def run():
    # Проверка аргументов планирования
    delay_hours = 0
    for i, arg in enumerate(sys.argv):
        if arg == "--delay-hours" and i + 1 < len(sys.argv):
            delay_hours = int(sys.argv[i+1])

    log(f"--- Starting Debug Playwright Script (Delay: {delay_hours}h) ---")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Change to False if you were local
        
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Load Cookies
        if os.path.exists(COOKIES_FILE):
            log(f"Loading cookies from {COOKIES_FILE}...")
            with open(COOKIES_FILE, "r") as f:
                cookies = json.load(f)
                cleaned = []
                for c in cookies:
                    cleaned.append({
                        "name": c["name"],
                        "value": c["value"],
                        "domain": c.get("domain", ".rutube.ru"),
                        "path": c.get("path", "/"),
                        "secure": c.get("secure", True)
                    })
                try:
                    context.add_cookies(cleaned)
                    log("✅ Cookies injected.")
                except Exception as e:
                    log(f"⚠️ Error injecting cookies: {e}")

        page = context.new_page()

        # --- SETUP LOGGING LISTENERS ---
        page.on("console", lambda msg: log(f"BROWSER CONSOLE: {msg.text}"))
        page.on("pageerror", lambda exc: log(f"BROWSER ERROR: {exc}"))
        page.on("requestfailed", lambda req: log(f"NET FAIL: {req.url} - {req.failure}"))
        # -------------------------------

        target_url = "https://studio.rutube.ru/videos/?show_moderation=1&ordering=calculated_date_asc#shorts"
        log(f"Navigating to {target_url}")
        
        try:
            page.goto(target_url, timeout=120000)
            page.wait_for_load_state("networkidle", timeout=120000)
        except Exception as e:
            log(f"Navigation error: {e}")
            page.screenshot(path="debug_nav_error.png")
            return

        if "login" in page.url or "multipass" in page.url:
            log("❌ Redirected to login page! Cookies might be dead.")
            page.screenshot(path="debug_login_redirect.png")
            return

        log(f"Page Title: {page.title()}")
        page.screenshot(path="debug_step1_loaded.png")

        # Create dummy video if missing
        if not os.path.exists(VIDEO_FILE):
             with open(VIDEO_FILE, "wb") as f:
                 f.write(os.urandom(2 * 1024 * 1024)) # 2MB to be sure

        try:
            # CLICK ADD
            add_btn = page.locator("button:has-text('Добавить')")
            if add_btn.is_visible():
                log("Found 'Добавить', clicking...")
                add_btn.click()
                page.wait_for_timeout(2000)
                page.screenshot(path="debug_step2_dropdown.png")
            else:
                log("❌ 'Добавить' button not found!")
                page.screenshot(path="debug_error_no_add.png")
                return

            # CLICK UPLOAD VIDEO
            # Found exact text from dump: "Загрузить видео или Shorts"
            upload_menu = page.locator("text='Загрузить видео или Shorts'")
            
            if upload_menu.count() > 0:
                # Use first visible
                upload_menu = upload_menu.first
                log(f"Found upload menu item: {upload_menu.inner_text()}")
                upload_menu.click()
                page.wait_for_timeout(3000) # Wait for modal animation
                page.screenshot(path="debug_step3_modal.png")
            else:
                log("❌ 'Загрузить видео или Shorts' item not found.")
                return

            # CLICK SELECT FILE (Inside Modal)
            # Try specific selector for the modal button
            file_btn = page.locator("div[role='dialog'] button:has-text('Выбрать файлы')")
            if not file_btn.is_visible():
                # Fallback to generic
                file_btn = page.locator("button:has-text('Выбрать файлы')")

            if file_btn.is_visible():
                log("Found 'Выбрать файлы', triggering file chooser...")
                with page.expect_file_chooser(timeout=15000) as fc_info:
                    file_btn.click()
                
                file_chooser = fc_info.value
                log(f"Setting file: {VIDEO_FILE}")
                file_chooser.set_files(VIDEO_FILE)
            else:
                log("❌ 'Выбрать файлы' button not found in modal.")
                page.screenshot(path="debug_error_no_file_btn.png")
                return

            # WAIT FOR UPLOAD & FILL FORM
            log("File set. Waiting for form to appear...")
            page.wait_for_timeout(5000)
            # Screenshot to confirm form appearance
            page.screenshot(path="debug_step4_form.png")

            # 1. FILL TITLE (Selector from provided HTML: input[name='title'])
            try:
                log("Filling Title...")
                video_title = f"Video Upload {datetime.datetime.now()}"
                
                # Попытка прочитать название из мета-файла (от синхронизатора)
                meta_path = os.path.join(os.path.dirname(__file__), "video_meta.json")
                if os.path.exists(meta_path):
                    with open(meta_path, "r") as f:
                        meta = json.load(f)
                        video_title = meta.get("title", video_title)
                
                page.locator("input[name='title']").fill(video_title)
                log(f"✅ Title filled with: {video_title}")
            except Exception as e:
                log(f"❌ Error filling title: {e}")

            # 2. FILL DESCRIPTION (Selector: textarea[name='description'])
            try:
                if page.locator("textarea[name='description']").is_visible():
                    page.locator("textarea[name='description']").fill("Uploaded automatically via Playwright agent.")
                    log("✅ Description filled.")
            except:
                pass

            # 3. SELECT CATEGORY (Mandatory)
            # Logic: Click the text "Выберите категорию" or the arrow, then click the first option
            try:
                log("Selecting Category...")
                # Try to find the dropdown trigger. 
                # Based on HTML: span text="Выберите категорию" inside a div
                dropdown_trigger = page.locator("span:has-text('Выберите категорию')").first
                if not dropdown_trigger.is_visible():
                     dropdown_trigger = page.locator("div[role='combobox']").first
                
                if dropdown_trigger.is_visible():
                    dropdown_trigger.click()
                    page.wait_for_timeout(1000)
                    # Select first option in the list
                    page.keyboard.press("ArrowDown")
                    page.keyboard.press("Enter")
                    log("✅ Category selected.")
                else:
                    log("⚠️ Category dropdown not found.")
            except Exception as e:
                 log(f"Error selecting category: {e}")

            # 4. SELECT "PUBLISH NOW" (Important for external scheduling)
            # Selector: input[value='now']
            try:
                # We need to click the label or the control, as input might be hidden
                now_radio = page.locator("input[value='now']")
                if now_radio.is_visible():
                    now_radio.click()
                else:
                    # Click parent label
                    page.locator("text='Сейчас'").click()
                log("✅ 'Publish Now' selected.")
            except:
                log("⚠️ Could not select 'Now', proceeding (might be default).")

            # WAIT FOR "UPLOAD COMPLETED" or "READY TO SAVE"
            # Often there is a progress bar. We should wait a bit.
            log("Waiting 60s for upload processing...")
            page.wait_for_timeout(60000)

            # CHECK FOR UPLOAD ERRORS
            error_indicator = page.locator("text='Не загружено'").or_(page.locator("text='Ошибка'")).or_(page.locator("text='Проверьте формат'"))
            if error_indicator.is_visible():
                log(f"❌ UPLOAD ERROR DETECTED ON PAGE: {error_indicator.first.inner_text()}")
                # Try to find the full error description
                error_desc = page.locator("p[class*='body-m-regular']").all_inner_texts()
                log(f"Full Error Text: {error_desc}")
                page.screenshot(path="debug_upload_error.png")
                return

            # CLICK SAVE
            save_btn = page.locator("button[type='submit']").last
            
            if save_btn.is_visible():
                if save_btn.is_disabled():
                    log("⚠️ Save button is DISABLED. Upload might still be in progress.")
                    # DUMP HTML to debug why
                    with open("rutube_form_dump.html", "w") as f:
                        f.write(page.content())
                    log("Saved HTML dump to rutube_form_dump.html")
                    
                    page.screenshot(path="debug_save_disabled.png")
                    # Wait loop
                    for i in range(10):
                        log(f"Waiting for button enable... {i+1}/10")
                        page.wait_for_timeout(3000)
                        if not save_btn.is_disabled():
                            break
                
                log("Clicking Save/Publish...")
                save_btn.click()
                
                # CRITICAL: WAIT FOR SUCCESS
                log("Waiting for result (30s)...")
                page.wait_for_timeout(5000)
                page.screenshot(path="debug_step5_after_save.png")
                
                # Check for error toasts
                error_toast = page.locator("div[class*='notification'][class*='error']")
                if error_toast.is_visible():
                    log(f"❌ ERROR TOAST: {error_toast.inner_text()}")
                
                # Check for success indicators
                # E.g., Modal closed, or URL changed, or 'Saved' text
                page.wait_for_timeout(25000)
                page.screenshot(path="debug_step6_final.png")
                log("Finished waiting.")
            else:
                log("❌ Save button not found.")
                page.screenshot(path="debug_error_no_save.png")

        except Exception as e:
            log(f"❌ CRITICAL ERROR: {e}")
            page.screenshot(path="debug_critical_error.png")

        browser.close()
        log("Browser closed.")

if __name__ == "__main__":
    run()

