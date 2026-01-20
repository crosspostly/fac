# Rutube API Guide

This document provides a brief overview of working with the Rutube API based on the scripts in this project.

## Authentication

Authentication is token-based. You can obtain a token by sending a POST request with your username and password to `https://rutube.ru/api/accounts/token_auth/`.

See `check_status.py` for a minimal example.

## Video Upload

There are three implemented methods for video upload, but only one is considered reliable.

### Method 1: Upload via URL (Reliable & Recommended)

This is the official method described in the API documentation.

**Workflow:**
1.  Make the video file accessible via a public URL. This is best achieved by running the local `server_simple.py`.
2.  Send a POST request to `https://rutube.ru/api/video/` with a JSON payload containing the `url`, `title`, `description`, etc.
3.  **CRITICAL:** The `PUBLIC_IP` variable in `config.py` **MUST** be replaced with a proper, publicly accessible **domain name**. Using a bare IP address will cause the download to fail or hang indefinitely, as Rutube's servers may not work correctly with IPs for callbacks or downloads.
4.  **CRITICAL:** The payload must include a `callback_url` that points to a webhook endpoint on your server. This URL must also use the domain name. The `server_simple.py` has a `/webhook` endpoint for this purpose. Rutube uses this callback to signal that the download is complete, which is necessary to start the video processing.
5.  After the initial request, you must poll the `https://rutube.ru/api/video/{video_id}/` endpoint until the `status` field becomes `ready`.

The `upload_and_verify.py` script implements this full, correct workflow.

### Method 2: Direct File Upload (Forbidden)

- **Script:** `fix_upload.py`
- **Description:** This method attempts to first create a draft and then upload the file directly via `multipart/form-data`.
- **Result:** This method is **not viable**. The API returns a `403 Forbidden` error, indicating that the user account does not have permission for this type of upload.

### Method 3: Playwright Browser Automation (Fragile)

- **Script:** `auth_playwright.py`
- **Description:** This method uses a headless browser to simulate a user uploading a video through the Rutube Studio web interface.
- **Result:** While it can bypass API limitations, it is extremely fragile and will break if Rutube changes its website's design. It should only be used as a last resort.