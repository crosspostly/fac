I found the cause of the issue and applied the requested logic.

### 1. 🛠️ Fixed Crash (Reason for "No New Videos")
The logs (`scheduler.log`) showed that the sync script was crashing immediately due to a missing library: `ModuleNotFoundError: No module named 'playwright'`.
- I successfully installed `playwright` and the required browser engines.
- The script now runs correctly without errors.

### 2. 🧠 Implemented "Smart Search Expansion"
I updated `sync_production.py` with your requested logic:
- **Standard Check:** It first checks the **top 5** videos.
- **Idle Detection:** If all top 5 are synced **AND** the latest video is older than **7 days**, it assumes the channel has been quiet.
- **Expanded Search:** In this case, it automatically expands the search to the **top 50** videos to catch any older, unpublished content you might have missed.

### 3. 📝 Full Description Support
Fixed an issue where video descriptions on Rutube were being truncated (ending with `...`).
- **Old Behavior:** Descriptions were taken from the flat playlist scan, which YouTube often truncates.
- **New Behavior:** When a new video is found, the script performs a separate metadata fetch (`get_full_video_info`) to get the **entire description text**.
- **Result:** All videos are now published with complete, original descriptions.

### 4. ✅ Verified
I manually ran the updated script. It successfully detected a missing video ("Ванга назвала 6 знаков..."), fetched its **full metadata**, uploaded it via API, and set the cover frame via Playwright.

> **⚠️ Note on Thumbnails:**
> I noticed in your memory logs that `rutube_cookies.json` expired on **Jan 5, 2026**.
> While video uploading will work (it uses the API), setting the **custom thumbnail** might fail until you update these cookies, as that part of the script uses browser automation.