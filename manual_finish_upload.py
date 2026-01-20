import os
import sys
import logging
from social_uploader import process_social_uploads

# ID видео, которое зависло
VIDEO_ID = "As-kuq_E8og"
VIDEO_PATH = f"uploads/{VIDEO_ID}.mp4"
TITLE = "Медовая морковь с лабне" # Взял из лога
DESCRIPTION = "Автоматическая загрузка. #food #cooking"

logging.basicConfig(level=logging.INFO)

if os.path.exists(VIDEO_PATH):
    print(f"✅ Файл найден: {VIDEO_PATH}")
    process_social_uploads(VIDEO_PATH, TITLE, DESCRIPTION)
    print("🎉 Ручная до-загрузка завершена.")
else:
    print(f"❌ Файл {VIDEO_PATH} не найден. Возможно, ID другой.")
