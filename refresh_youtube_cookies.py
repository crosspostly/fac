#!/usr/bin/env python3
"""Auto-refresh YouTube cookies using Playwright with Session Keep-Alive"""

import asyncio
import os
import sys
import time
from playwright.async_api import async_playwright

COOKIE_FILE_PATH = 'youtube_cookies.txt'
NEW_COOKIE_FILE_PATH = 'youtube_cookies_new.txt'

def parse_netscape_cookies(content):
    """Parse Netscape cookie file content into a list of dicts for Playwright"""
    cookies = []
    for line in content.splitlines():
        if line.startswith('#') or not line.strip():
            continue
        
        parts = line.strip().split('\t')
        if len(parts) >= 7:
            # Netscape format: domain, flag, path, secure, expiry, name, value
            domain = parts[0]
            # secure = parts[3] == 'TRUE'
            expires = int(parts[4]) if parts[4].isdigit() else 0
            name = parts[5]
            value = parts[6]
            path = parts[2]
            
            cookie = {
                'name': name,
                'value': value,
                'domain': domain,
                'path': path,
                'expires': expires,
                'secure': parts[3] == 'TRUE'
            }
            cookies.append(cookie)
    return cookies

async def refresh_youtube_cookies():
    email = os.getenv('YOUTUBE_EMAIL')
    password = os.getenv('YOUTUBE_PASSWORD')
    
    # Try to read existing cookies from ENV or File
    existing_cookies_txt = os.getenv('YOUTUBE_COOKIES_TXT', '')
    if not existing_cookies_txt and os.path.exists(COOKIE_FILE_PATH):
        with open(COOKIE_FILE_PATH, 'r') as f:
            existing_cookies_txt = f.read()

    async with async_playwright() as p:
        # Launch with stealth-like args
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        # 1. Inject existing cookies if available
        if existing_cookies_txt:
            print("[1/5] 🍪 Injecting existing cookies...")
            try:
                cookies_list = parse_netscape_cookies(existing_cookies_txt)
                if cookies_list:
                    # Clean domain for Playwright (remove leading dots sometimes helps, but strict matching is better)
                    # Playwright expects domains exactly.
                    await context.add_cookies(cookies_list)
                    print(f"   ✅ Injected {len(cookies_list)} cookies.")
            except Exception as e:
                print(f"   ⚠️ Failed to parse/inject cookies: {e}")

        page = await context.new_page()
        
        try:
            print("[2/5] 🌍 Opening YouTube...")
            await page.goto('https://www.youtube.com', wait_until='domcontentloaded')
            
            # Handling Consent Popups (Before Login Check)
            try:
                # "Accept all" button usually
                accept_btn = page.locator('button[aria-label="Accept all"], button:has-text("Accept all"), button:has-text("Принять все")')
                if await accept_btn.count() > 0 and await accept_btn.is_visible():
                    print("   🍪 Clicking Cookie Consent...")
                    await accept_btn.first.click()
                    await page.wait_for_timeout(2000)
            except:
                pass

            await page.wait_for_load_state('networkidle')
            
            # 2. Check Login Status
            is_logged_in = False
            try:
                # Avatar button usually indicates logged in state
                await page.wait_for_selector('#avatar-btn, button[aria-label="Account profile photo"], img[alt="Avatar image"]', timeout=8000)
                print("[3/5] ✅ Already logged in! Session is valid.")
                is_logged_in = True
            except:
                print("[3/5] ⚠️ Not logged in (Session expired or missing).")

            # 3. Login Attempt (Only if not logged in)
            if not is_logged_in:
                if not email or not password:
                    print("   ❌ No credentials provided for re-login. Aborting.")
                    return False
                
                print("   🔄 Attempting fresh login (Risk of Captcha)...")
                # Click sign in
                try:
                    signin_btn = page.locator('a[href*="accounts.google.com"]')
                    if await signin_btn.count() > 0:
                        await signin_btn.first.click()
                    else:
                        await page.goto('https://accounts.google.com/ServiceLogin?service=youtube')
                except:
                    await page.goto('https://accounts.google.com/ServiceLogin?service=youtube')
                
                await page.wait_for_load_state('networkidle')
                
                # Email
                try:
                    await page.fill('input[type="email"]', email)
                    await page.press('input[type="email"]', 'Enter')
                    await page.wait_for_timeout(3000)
                except Exception as e:
                    print(f"   ❌ Failed to enter email: {e}")
                    return False

                # Password
                try:
                    await page.fill('input[type="password"]', password)
                    await page.press('input[type="password"]', 'Enter')
                    await page.wait_for_url('**/youtube.com/**', timeout=20000)
                    print("   ✅ Login successful (redirected to YT).")
                except Exception as e:
                    print(f"   ❌ Login failed (Captcha/2FA likely): {e}")
                    await page.screenshot(path='login_failed.png')
                    return False

            # 4. Refresh/Activity
            print("[4/5] 🔄 refreshing page to update tokens...")
            await page.reload(wait_until='networkidle')
            await page.wait_for_timeout(3000)
            
            # 5. Export Cookies
            print("[5/5] 💾 Extracting and saving new cookies...")
            cookies = await context.cookies()
            
            if not cookies:
                print("ERROR: No cookies found to export!")
                return False
            
            netscape_cookies = convert_to_netscape_format(cookies)
            
            with open(NEW_COOKIE_FILE_PATH, 'w') as f:
                f.write(netscape_cookies)
            
            print(f"SUCCESS! Exported {len(cookies)} cookies to {NEW_COOKIE_FILE_PATH}")
            return True
        
        except Exception as e:
            print(f"CRITICAL ERROR: {e}")
            await page.screenshot(path='error_state.png')
            import traceback
            traceback.print_exc()
            return False
        finally:
            await browser.close()

def convert_to_netscape_format(cookies):
    """Convert Playwright cookies to Netscape format"""
    lines = [
        '# Netscape HTTP Cookie File',
        '# Generated by auto_refresh_cookies script',
        ''
    ]
    for cookie in cookies:
        # Netscape format: domain flag path secure expiry name value
        domain = cookie.get('domain', '')
        flag = 'TRUE' if domain.startswith('.') else 'FALSE'
        path = cookie.get('path', '/')
        secure = 'TRUE' if cookie.get('secure', False) else 'FALSE'
        expires = int(cookie.get('expires', time.time() + 31536000)) # Default 1 year if missing
        name = cookie.get('name', '')
        value = cookie.get('value', '')
        
        lines.append(f"{domain}\t{flag}\t{path}\t{secure}\t{expires}\t{name}\t{value}")
    
    return '\n'.join(lines)

if __name__ == '__main__':
    result = asyncio.run(refresh_youtube_cookies())
    sys.exit(0 if result else 1)
