from playwright.sync_api import sync_playwright
import json
import os
import time

# --- CONFIG ---
COOKIES_FILE = os.path.join(os.path.dirname(__file__), 'rutube_cookies.json')
# Rutube Internal ID
VIDEO_ID = "65ff523ab8be8fc5117ce1428d014e43" 
# Local File Path (YouTube ID based)
THUMB_PATH = os.path.join(os.path.dirname(__file__), 'uploads', 'k3og3K8DelY.jpg')

def set_thumbnail_playwright(video_id, thumb_path):
    print(f"🚀 Starting Playwright Thumbnail Upload for {video_id}...")
    
    if not os.path.exists(thumb_path):
        print(f"❌ Thumbnail file not found: {thumb_path}")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
        
        # Load cookies
        if os.path.exists(COOKIES_FILE):
            print(f"🍪 Loading cookies from {COOKIES_FILE}")
            with open(COOKIES_FILE, 'r') as f:
                context.add_cookies(json.load(f))
        
        page = context.new_page()
        page.set_default_timeout(90000)
        
        # 1. Navigate to Studio List
        list_url = "https://studio.rutube.ru/videos?show_moderation=1&ordering=calculated_date_asc&period=7_days&tab=main#video"
        print(f"🌍 Navigating to Studio List: {list_url}")
        
        try:
            page.goto(list_url)
            page.wait_for_load_state('domcontentloaded')
            page.wait_for_timeout(10000)
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            browser.close()
            return

        # 2. Find Video and Click Title
        print("🔍 Searching for video link...")
        links = page.locator("a")
        target = None
        
        # Search by ID in href
        for i in range(links.count()):
            href = links.nth(i).get_attribute("href")
            
            if href and video_id in href:
                print(f"🎯 Found target: {links.nth(i).inner_text().strip()}")
                target = links.nth(i)
                break
        
        if not target:
            print("❌ Video not found in the list.")
            browser.close()
            return

        print("🖱️ Clicking video title...")
        target.click()
        page.wait_for_timeout(5000) # Wait for modal
        
        # 3. Open Upload Dialog
        print("📸 Looking for 'Edit Cover' button...")
        try:
            # Button with pencil icon
            edit_cover_btn = page.locator("button[aria-label='Редактировать обложку']")
            if edit_cover_btn.count() == 0:
                print("⚠️ 'Edit Cover' button not found. Maybe 'Add Cover'?")
                # Fallback to any file input
                file_input = page.locator("input[type='file']").first
                file_input.set_input_files(thumb_path)
            else:
                print("✅ Found 'Edit Cover' button.")
                
                # Attempt 1: Check if clicking triggers File Chooser directly
                try:
                    with page.expect_file_chooser(timeout=3000) as fc_info:
                        edit_cover_btn.click()
                    file_chooser = fc_info.value
                    file_chooser.set_files(thumb_path)
                    print("✅ File chooser handled directly.")
                except:
                    print("⚠️ No direct file chooser. Checking for dropdown menu...")
                    # Attempt 2: Check for 'Загрузить' in dropdown
                    upload_menu = page.locator("text=Загрузить")
                    if upload_menu.count() > 0 and upload_menu.first.is_visible():
                        print("⬇️ Found 'Upload' menu item. Clicking...")
                        with page.expect_file_chooser() as fc_info:
                            upload_menu.first.click()
                        file_chooser = fc_info.value
                        file_chooser.set_files(thumb_path)
                    else:
                        print("⚠️ No 'Upload' menu found. Trying fallback to hidden input.")
                        # Attempt 3: Just find any file input
                        page.locator("input[type='file']").first.set_input_files(thumb_path)

            print("✅ File selected.")
            
            # 3.5 Handle Crop Modal (Кадрирование обложки)
            # After file upload, a "Crop" modal usually appears with a "Готово" button.
            print("✂️ Checking for Crop Modal...")
            try:
                # Wait for potential crop modal
                done_btn = page.locator("button:has-text('Готово')")
                # Wait a bit for animation
                page.wait_for_timeout(2000)
                
                if done_btn.count() > 0 and done_btn.first.is_visible():
                    print("✅ Found Crop Modal. Clicking 'Готово'...")
                    done_btn.first.click()
                    # Wait for crop modal to close
                    page.wait_for_timeout(2000)
                else:
                    print("ℹ️ No Crop Modal detected (or auto-closed).")
            except Exception as e:
                print(f"⚠️ Error handling crop modal: {e}")

            # 4. Save
            print("💾 Clicking Save...")
            save_btn = page.locator("button:has-text('Сохранить')")
            # ...
            if save_btn.is_enabled():
                # Use force=True to bypass potential overlays (like tooltips or toasts)
                save_btn.click(force=True)
                print("✅ Clicked Save (forced).")
                page.wait_for_timeout(5000)
                print("🎉 Saved successfully!")
            else:
                print("⚠️ Save button disabled. No changes detected?")
                
        except Exception as e:
            print(f"❌ Error during interaction: {e}")
            page.screenshot(path="debug_interaction_error.png")

        browser.close()