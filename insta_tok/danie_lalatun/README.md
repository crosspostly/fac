# Danie Lalatun - AI Model Project

This project automates content publishing to Instagram and TikTok using a unified scheduler.

## 📂 Project Structure

*   `content/`: Folder containing images (`.jpg`) and videos (`.mp4`).
*   `unified_scheduler.py`: **Main script.** Orchestrates posting to both platforms.
*   `instagram_poster.py`: Wrapper for `instagrapi` to handle IG login and upload.
*   `publish.py`: Wrapper for `tiktok-uploader` to handle TT upload.
*   `unified_posted_content.json`: Database of posted files to prevent duplicates.
*   `debug_instagram.py`: Diagnostic tool for login issues.
*   `.env`: Credentials (Login/Password).

## 🚀 How to Run

### 1. Unified Scheduler (Auto-Post)
Runs the check loop. If it's time to post (default: every 24h), it selects a random unposted file.

```bash
# Run from project root
../venv/bin/python unified_scheduler.py
```

**Logic:**
1.  Checks `last_post_date` in `unified_posted_content.json`.
2.  If time > 24h, selects random file from `content/`.
3.  **Instagram:** Attempts login (Session -> Password) and upload.
4.  **TikTok:** If video, runs `publish.py`.
5.  **Success:** If *at least one* platform works, saves file to DB as posted.

### 2. Manual TikTok Upload
```bash
../venv/bin/python publish.py "content/new_one/video.mp4" "Your Caption"
```

### 3. Debug Instagram
If you face login errors:
```bash
../venv/bin/python debug_instagram.py
```

## ⚠️ Current Status & Issues (Jan 16, 2026)

### Instagram (`blacklist` IP)
*   **Status:** Fails to login.
*   **Error:** "change your IP address, because it is added to the blacklist".
*   **Cause:** Instagram aggressively blocks data-center IPs (hosting servers) from logging in via mobile API.
*   **Solution Needed:**
    1.  **Proxy:** Add a residential/mobile proxy to `instagram_poster.py`.
    2.  **Session Import:** Login locally on a PC, generate `danie_lalatun.json` session, and upload it here.
    3.  **Cloudflare Warp:** Install Warp on server to change egress IP.

### TikTok
*   **Status:** **Operational**.
*   **Note:** Temporarily disabled in `unified_scheduler.py` (commented out) to focus on fixing Instagram. To enable, uncomment lines in `main()`.

## 🛠 Maintenance

**Resetting Posting History:**
To force the bot to repost existing files or reset the timer:
```bash
echo '{"posted_files": [], "last_post_date": null}' > unified_posted_content.json
```