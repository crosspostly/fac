import json
import time

TARGET_USER_ID = "69564892126"
TARGET_SESSION_ID = "69564892126%3A9s4cdGgKONpU8c%3A23%3AAYgW3X18Xmn3FKBr6fOIGBfoP6quapD8evsPEgP1rw"

settings = {
    "uuids": {
        "phone_id": "manual-phone-id-v2",
        "uuid": "manual-uuid-v2",
        "client_session_id": "manual-client-session-v2",
        "advertising_id": "manual-ad-id-v2",
        "android_device_id": "android-manual-id-v2",
    },
    "mid": "aWzJigALAAE-Fbxmp-tGStRLgeXP",
    "authorization_data": {
        "ds_user_id": TARGET_USER_ID,
        "sessionid": TARGET_SESSION_ID
    },
    "cookies": {
        "csrftoken": "CgKlJLDgdjGBg2g9DnRQrd",
        "datr": "kslsaTscwn9hrKGAI6b0m9ue",
        "dpr": "1.3020833730697632",
        "ds_user_id": TARGET_USER_ID,
        "ig_did": "6719FDA8-FA53-4D04-AFB5-246B66440D9D",
        "mid": "aWzJigALAAE-Fbxmp-tGStRLgeXP",
        "rur": "\"RVA,69564892126,1800277679:01fe728c669f36a77ed4ca4bb8331d9c2b5154f20a31c1f5beaa1a510f9dd58db6b658b2\"",
        "sessionid": TARGET_SESSION_ID,
        "wd": "747x737"
    },
    "last_login": time.time(),
    "device_settings": {
        "app_version": "269.0.0.18.75",
        "android_version": 29,
        "android_release": "10",
        "dpi": "420dpi",
        "resolution": "1080x1920",
        "manufacturer": "OnePlus",
        "device": "OnePlus6T",
        "model": "ONEPLUS A6013",
        "cpu": "qcom",
        "version_code": "314665256"
    },
    "user_agent": "Instagram 269.0.0.18.75 Android (29/10; 420dpi; 1080x1920; OnePlus; ONEPLUS A6013; OnePlus6T; qcom; en_US; 314665256)",
    "country": "US",
    "country_code": 1,
    "locale": "en_US",
    "timezone_offset": -14400
}

with open("insta_tok/pp_witch_session.json", "w") as f:
    json.dump(settings, f, indent=4)

print("✅ Файл сессии pp_witch создан с новым sessionid!")
