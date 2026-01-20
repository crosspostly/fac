import json

cookies_json = [
    {"name": "__Secure-3PSID", "value": "g.a0004gh9R_QShLSQ_xTcqJKyuGS24h_X9GOITx6iIrHqxNTr_1-qajoKElyt5XVm2FvG7PYimgACgYKAVISARcSFQHGX2Mib12SvXvB85r2LrggQKaFEBoVAUF8yKoM_tkULJ-6brQsgTGhoJE30076", "domain": ".youtube.com", "path": "/", "secure": True},
    {"name": "__Secure-1PSIDTS", "value": "sidts-CjUBflaCdVRCMKiNKxH62xK74w3l7f1aUINIn6sKOMxqXoFMTs91Kmd_GZ49mwe-xT5aVJvqfBAA", "domain": ".youtube.com", "path": "/", "secure": True},
    {"name": "SAPISID", "value": "_0HjJ4ba8_YosxB4/Ag0akUIANcnac88jP", "domain": ".youtube.com", "path": "/", "secure": True},
    {"name": "__Secure-1PSIDCC", "value": "AKEyXzWdiApzOcBT4GS9ibwrOTO26JOctl69_kep9MMeaumdezZBmS8z-jKJJjaVuZ7ITzDD2pE", "domain": ".youtube.com", "path": "/", "secure": True},
    {"name": "SSID", "value": "AbdHvVv3ZEZtvKgb-", "domain": ".youtube.com", "path": "/", "secure": True},
    {"name": "__Secure-1PAPISID", "value": "_0HjJ4ba8_YosxB4/Ag0akUIANcnac88jP", "domain": ".youtube.com", "path": "/", "secure": True},
    {"name": "__Secure-1PSID", "value": "g.a0004gh9R_QShLSQ_xTcqJKyuGS24h_X9GOITx6iIrHqxNTr_1-qVyCI5FL2QHBviNgK7tDmuAACgYKASoSARcSFQHGX2MiTBRZ_8uuR7_ug4h3OEQtLhoVAUF8yKrzwnBmbJlycstdFiOmBTjf0076", "domain": ".youtube.com", "path": "/", "secure": True},
    {"name": "__Secure-3PAPISID", "value": "_0HjJ4ba8_YosxB4/Ag0akUIANcnac88jP", "domain": ".youtube.com", "path": "/", "secure": True},
    {"name": "__Secure-3PSIDCC", "value": "AKEyXzUkSc3soh7VA3EOpSGogqLYBqfqXdizHpb0tRtBsfYR-qKPyYZUBuEYhy4j_HAHX-0LZw", "domain": ".youtube.com", "path": "/", "secure": True},
    {"name": "__Secure-3PSIDTS", "value": "sidts-CjUBflaCdVRCMKiNKxH62xK74w3l7f1aUINIn6sKOMxqXoFMTs91Kmd_GZ49mwe-xT5aVJvqfBAA", "domain": ".youtube.com", "path": "/", "secure": True},
    {"name": "LOGIN_INFO", "value": "AFmmF2swRAIgXelCzMlGJ21235x5d9GJcQ7m7gFkgdBUhg87UM-vTEwCIERXW8bmrbLTZGWjUyhv1pcGxNriDA46C3e6UuDkk4Ge:QUQ3MjNmeG9pemJ5bVlmaEtJUXM3VklJNjVyaDRjaFVPMjNmaTdtX1J3bFZRSC1ndVp2SnVmYndjd1V1S1MxSnlzQmhtbXJGUnRIVmdUWEpFemRFYllnRGI1Nlg3VWh3UjQ5WlVUb3JYSS0wUTFKOTFVWXZFQU1qWmZhejN6UU9VNE9UbG8zTkctZ3VFUjhZMFF4dzN1N1dON0VreFNNdUlB", "domain": ".youtube.com", "path": "/", "secure": True},
    {"name": "PREF", "value": "f4=4000000&tz=Europe.Moscow&f7=10100&f6=40080000&repeat=NONE&f5=30000", "domain": ".youtube.com", "path": "/", "secure": True},
    {"name": "SOCS", "value": "CAAaBgiA6czGBg", "domain": ".youtube.com", "path": "/", "secure": True}
]

with open("youtube_cookies.txt", "w") as f:
    f.write("# Netscape HTTP Cookie File\n")
    for c in cookies_json:
        domain = c['domain']
        include_sub = "TRUE" if domain.startswith(".") else "FALSE"
        path = c['path']
        secure = "TRUE" if c['secure'] else "FALSE"
        expiry = "0" # Session or future
        name = c['name']
        value = c['value']
        f.write(f"{domain}\t{include_sub}\t{path}\t{secure}\t{expiry}\t{name}\t{value}\n")

print("✅ youtube_cookies.txt created.")
