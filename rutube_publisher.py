from playwright.sync_api import sync_playwright
import json
import os
import time
import sys

COOKIES_FILE = 'rutube_cookies.json'

def publish_video(video_id):
    print(f"[Playwright] Making video {video_id} PUBLIC...")
    
    if not os.path.exists(COOKIES_FILE):
        print("❌ Cookies file not found.")
        return False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Headless mode
        context = browser.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
        
        # Load cookies
        with open(COOKIES_FILE, 'r') as f:
            cookies = json.load(f)
            context.add_cookies(cookies)

        page = context.new_page()
        
        # Go to Video Edit Page
        url = f"https://studio.rutube.ru/video/{video_id}"
        print(f"Loading {url}...")
        try:
            page.goto(url, timeout=60000)
            page.wait_for_load_state('networkidle')
        except Exception as e:
            print(f"❌ Failed to load page: {e}")
            page.screenshot(path="error_load.png")
            browser.close()
            return False

        # Debug screenshot
        page.screenshot(path=f"debug_studio_{video_id}.png")

        try:
            # 1. Look for Privacy Dropdown
            # Usually it's a combobox or a radio button group.
            # Based on experience, it might be a text "Доступ по прямой ссылке" or similar that opens a dropdown.
            
            # Wait for any characteristic element of the edit form
            page.wait_for_selector("input[name='title']", timeout=20000)
            print("✅ Edit form loaded.")

            # Try to find the "Access" section.
            # It often defaults to "Скрытый" or "Доступ по ссылке".
            # We look for the text of the current state or the label.
            
            # Strategy: Find the dropdown that controls visibility
            # Let's look for text "Доступ" and find a sibling or child
            
            # Click the Access Dropdown (Assuming it shows current status like "Скрытый" or "Доступ по ссылке")
            # We can try clicking the element that has text "Доступ"
            
            # More robust: Look for specific radio buttons if they are exposed, or the dropdown trigger.
            # Let's try to find the dropdown by common container classes or text.
            
            access_trigger = page.locator("div[class*='access-selector']").first
            if not access_trigger.is_visible():
                # Fallback: Search by text "Доступ" and hope it clicks the dropdown
                # Often in Rutube Studio there is a block "Параметры доступа"
                print("Searching for Access dropdown...")
                # This is a guess based on typical React UI libraries used by Rutube
                access_trigger = page.locator("text='Доступ по ссылке'") 
                if not access_trigger.is_visible():
                     access_trigger = page.locator("text='Скрытый'")
            
            if access_trigger.is_visible():
                access_trigger.click()
                print("Clicked Access dropdown.")
            else:
                # Last resort: Try to find any combobox that might be it
                print("⚠️ Access trigger not found easily. Analyzing page text...")
                # page.content() could be analyzed here
            
            # Select "Открытый доступ" (Public)
            public_option = page.locator("text='Открытый доступ'")
            if public_option.is_visible():
                public_option.click()
                print("✅ Selected 'Открытый доступ'")
            else:
                # Maybe it's a radio button?
                radio_public = page.locator("input[value='public']")
                if radio_public.count() > 0:
                     radio_public.check()
                     print("✅ Checked 'Public' radio")
                else:
                    print("❌ Could not find 'Public' option.")
                    page.screenshot(path="error_access_menu.png")
                    browser.close()
                    return False

            # Click Save
            # Button usually says "Сохранить"
            save_btn = page.locator("button:has-text('Сохранить')")
            if save_btn.is_visible() and save_btn.is_enabled():
                save_btn.click()
                print("Pressed Save.")
                page.wait_for_timeout(3000) # Wait for save
            else:
                print("⚠️ Save button not found or disabled (maybe already public?).")

            print(f"✅ Video {video_id} should now be public.")
            browser.close()
            return True

        except Exception as e:
            print(f"❌ Playwright Error: {e}")
            page.screenshot(path="error_main.png")
            browser.close()
            return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python rutube_publisher.py <video_id>")
    else:
        publish_video(sys.argv[1])
