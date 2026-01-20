import json
import time
from playwright.sync_api import sync_playwright

# Новые куки (без sessionid)
RAW_COOKIES = [{"domain":".instagram.com","expirationDate":1796905937.624155,"hostOnly":False,"httpOnly":True,"name":"ig_did","path":"/","sameSite":"None","secure":True,"value":"A7B77662-1BDE-47A2-82C6-2AF21B8E70AC"},{"domain":".instagram.com","expirationDate":1799930025.204287,"hostOnly":False,"httpOnly":True,"name":"ps_l","path":"/","sameSite":"Lax","secure":True,"value":"1"},{"domain":".instagram.instagram.com","expirationDate":1799930025.204491,"hostOnly":False,"httpOnly":True,"name":"ps_n","path":"/","sameSite":"None","secure":True,"value":"1"},{"domain":".instagram.com","expirationDate":1799930094.642736,"hostOnly":False,"httpOnly":True,"name":"datr","path":"/","sameSite":"None","secure":True,"value":"7Wg5aRq2-jSfGodjLH-_ygHr"},{"domain":".instagram.com","expirationDate":1799930109,"hostOnly":False,"httpOnly":False,"name":"mid","path":"/","sameSite":"Lax","secure":True,"value":"aTlo7QALAAGchQW80cx0KMzOt-3F"},{"domain":".instagram.com","expirationDate":1796906111.598544,"hostOnly":False,"httpOnly":False,"name":"ig_nrcb","path":"/","sameSite":"Lax","secure":True,"value":"1"},{"domain":".instagram.com","expirationDate":1769343208,"hostOnly":False,"httpOnly":False,"name":"dpr","path":"/","sameSite":"None","secure":True,"value":"1.3020833730697632"},{"domain":".instagram.com","expirationDate":1769343218,"hostOnly":False,"httpOnly":False,"name":"wd","path":"/","sameSite":"Lax","secure":True,"value":"1451x736"},{"domain":".instagram.com","expirationDate":1803299503.680054,"hostOnly":False,"httpOnly":False,"name":"csrftoken","path":"/","sameSite":"Lax","secure":True,"value":"8tQd4KCnD5nnxDOO0ExdY150eIWWsg4s"},{"domain":".instagram.com","expirationDate":1776514423.513532,"hostOnly":False,"httpOnly":False,"name":"ds_user_id","path":"/","sameSite":"None","secure":True,"value":"69564892126"},{"domain":".instagram.com","hostOnly":False,"httpOnly":True,"name":"rur","path":"/","sameSite":"Lax","secure":True,"value":"\"RVA\05469564892126\0541800274423:01fe41bd5d4ffb4d90d558b9fcc029355993fb93ec99b4fed0ad2d7490cd201ed9e849e5\""}]

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
        context.add_cookies(RAW_COOKIES)
        page = context.new_page()

        print("🌍 Пробую зайти в Инстаграм с неполными куками...")
        page.goto("https://www.instagram.com/", wait_until="networkidle")
        time.sleep(5)
        
        # Делаем скриншот, чтобы понять, где мы
        page.screenshot(path="debug_insta_revive.png")
        
        body_text = page.inner_text("body")
        print("\nТЕКСТ НА ЭКРАНЕ:")
        print('\n'.join([l.strip() for l in body_text.splitlines() if l.strip()][:20]))
        
        # Проверяем, не появился ли sessionid
        cookies = context.cookies()
        session_id = next((c['value'] for c in cookies if c['name'] == 'sessionid'), None)
        
        if session_id:
            print(f"✅ УРА! Инстаграм выдал sessionid: {session_id[:10]}...")
            # Сохраняем сессию для бота
            settings = {
                "authorization_data": {"ds_user_id": "69564892126", "sessionid": session_id},
                "cookies": {c['name']: c['value'] for c in cookies}
            }
            with open("insta_tok/pp_witch_session.json", "w") as f:
                json.dump(settings, f, indent=4)
            print("💾 Сессия сохранена!")
        else:
            print("❌ sessionid всё еще нет. Нужно войти вручную.")

        browser.close()

if __name__ == "__main__":
    run()
