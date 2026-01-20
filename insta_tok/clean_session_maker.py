import json
import time

TARGET_USER_ID = "69564892126"
TARGET_SESSION_ID = "69564892126%3AYboVkccADo6zWs%3A22%3AAYi7jJYSlB-WpMdmHPJC03hWs35iXMOLDtmDnWsFBQ"
TARGET_CSRF = "8tQd4KCnD5nnxDOO0ExdY150eIWWsg4s"

settings = {
    "uuids": {
        "phone_id": "samsung-phone-id",
        "uuid": "samsung-uuid",
        "client_session_id": "samsung-client-session",
        "advertising_id": "samsung-ad-id",
        "android_device_id": "samsung-android-id",
    },
    "mid": "aTlo7QALAAGchQW80cx0KMzOt-3F",
    "authorization_data": {
        "ds_user_id": TARGET_USER_ID,
        "sessionid": TARGET_SESSION_ID
    },
    "cookies": {
        "ds_user_id": TARGET_USER_ID,
        "sessionid": TARGET_SESSION_ID,
        "csrftoken": TARGET_CSRF,
        "ig_did": "A7B77662-1BDE-47A2-82C6-2AF21B8E70AC",
        "mid": "aTlo7QALAAGchQW80cx0KMzOt-3F",
        "ig_nrcb": "1",
        "dpr": "1.3020833730697632",
        "rur": "\"RVA,69564892126,1800274423:01fe41bd5d4ffb4d90d558b9fcc029355993fb93ec99b4fed0ad2d7490cd201ed9e849e5\"",
        "wd": "1440x3088"
    },
    "last_login": time.time(),
    "device_settings": {
        "app_version": "269.0.0.18.75",
        "android_version": 31,
        "android_release": "12",
        "dpi": "480dpi",
        "resolution": "1440x3088",
        "manufacturer": "samsung",
        "device": "SM-S908B",
        "model": "SM-S908B",
        "cpu": "exynos2200",
        "version_code": "314665256"
    },
    "user_agent": "Instagram 269.0.0.18.75 Android (31/12; 480dpi; 1440x3088; samsung; SM-S908B; SM-S908B; exynos2200; en_US; 314665256)",
    "country": "US",
    "country_code": 1,
    "locale": "en_US",
    "timezone_offset": -14400
}

session_path = "insta_tok/pp_witch_session.json"
with open(session_path, "w") as f:
    json.dump(settings, f, indent=4)

print(f"✅ Файл {session_path} обновлен под Samsung S22.")
