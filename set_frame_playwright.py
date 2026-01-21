from playwright.sync_api import sync_playwright
import json
import os
import time

# --- CONFIG ---
COOKIES_FILE = os.path.join(os.path.dirname(__file__), 'rutube_cookies.json')

def set_cover_frame(video_id, title_hint=""):
    """
    Opens the Rutube Studio video editor and sets the cover frame to 00:01.
    """
    print(f"🚀 Setting cover frame (00:01) for video {video_id}...")
    
    if not os.path.exists(COOKIES_FILE):
        print("❌ Cookies file not found!")
        return False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
        
        with open(COOKIES_FILE, 'r') as f:
            context.add_cookies(json.load(f))
        
        page = context.new_page()
        page.set_default_timeout(90000)
        
        # 1. Navigate to List
        # Changed ordering to DESC to see newest videos first
        list_url = "https://studio.rutube.ru/videos?show_moderation=1&ordering=calculated_date_desc&period=7_days&tab=main#video"
        print(f"🌍 Navigating to Studio List: {list_url}")
        
        try:
            page.goto(list_url)
            page.wait_for_load_state('domcontentloaded')
            page.wait_for_timeout(5000)
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            browser.close()
            return False

        # 2. Find Video
        print("🔍 Searching for video...")
        links = page.locator("a")
        target = None
        for i in range(links.count()):
            href = links.nth(i).get_attribute("href")
            text = links.nth(i).inner_text().strip()
            if (href and video_id in href) or (title_hint and title_hint in text):
                print(f"🎯 Found target: {text}")
                target = links.nth(i)
                break
        
        if not target:
            print("❌ Video not found in the list.")
            browser.close()
            return False

        print("🖱️ Clicking video title...")
        target.click()
        page.wait_for_timeout(5000)

        # 3. Open Frame Select
        print("📸 Clicking 'Select frame' button...")
        try:
            # Selector for the "Select frame" button (Film icon)
            btn = page.locator("button[aria-label='Выбрать кадр из видео']")
            btn.click()
            page.wait_for_timeout(3000)
            
            # 4. Set Time to 00:01
            print("⏱️ Setting time to 00:01...")
            # Locate the spinbuttons. Usually 2 (MM:SS) or 3 (HH:MM:SS)
            spinners = page.locator('div[role="spinbutton"]')
            if spinners.count() > 0:
                # Target the last spinner (Seconds)
                seconds_input = spinners.last
                seconds_input.click()
                page.wait_for_timeout(500)
                # Clear and type "01"
                # Backspace x2 to clear any existing digits (usually 00)
                page.keyboard.press("Backspace")
                page.keyboard.press("Backspace")
                page.keyboard.type("01")
                page.wait_for_timeout(1000)
                print("   ✅ Time input updated.")
            else:
                print("⚠️ Spinners not found. Default frame (00:00) will be used.")

            # 5. Confirm Frame Selection
            print("   💾 Clicking 'Done' (Готово)...")
            # Look for the 'Готово' button in the modal footer
            done_btn = page.locator("button:has-text('Готово')")
            if done_btn.count() > 0:
                done_btn.first.click()
                print("   ✅ Frame selection confirmed.")
                page.wait_for_timeout(2000)
            else:
                print("❌ 'Done' button not found!")

            # 6. Save Changes (Main Modal)
            print("💾 Clicking Main Save...")
            main_save = page.locator("button:has-text('Сохранить')").first
            
            # Force click is crucial here as the button might be covered by overlays
            if main_save.is_visible():
                main_save.click(force=True)
                print("🎉 Main Saved (Forced Click)!")
                page.wait_for_timeout(3000)
            else:
                print("⚠️ Save button not visible or disabled.")

        except Exception as e:
            print(f"❌ Error during UI interaction: {e}")
            browser.close()
            return False

        browser.close()
        return True

if __name__ == "__main__":
    import sys
    vid = sys.argv[1] if len(sys.argv) > 1 else "65ff523ab8be8fc5117ce1428d014e43"
    set_cover_frame(vid, "Алхимия Власти")
