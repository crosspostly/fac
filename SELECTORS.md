# Rutube UI Selectors & Automation Guide

If the API fails, we can use Browser Automation (Playwright/Puppeteer). Below are the target selectors for the **Studio/Upload** flow.

## 1. Login Flow (`https://rutube.ru/login`)

| Element | Selector Strategy | Notes |
| :--- | :--- | :--- |
| **Login Button** | `button[class*='header__login-button']` | Main page header |
| **Phone Input** | `input[type='tel']` | Usually inside the auth modal |
| **Password Input** | `input[type='password']` | Appears after phone entry |
| **Submit Button** | `button[type='submit']` | Used for both steps |

## 2. Upload Flow (`https://studio.rutube.ru/videos/upload`)

| Action | Selector / Strategy | Notes |
| :--- | :--- | :--- |
| **Add Button** | `button:has-text("Добавить")` | Top header |
| **Upload Menu Item** | `text="Загрузить видео или Shorts"` | Dropdown item |
| **File Input** | `input[type='file']` | Use `set_input_files` |
| **Title** | `input[name='title']` | |
| **Description** | `textarea[name='description']` | |
| **Category** | `div[role='combobox']:has-text('Выберите категорию')` | Click then select item |
| **Access** | `div[role='combobox']:has-text('Доступ')` | |
| **Schedule Toggle** | `input[value='delayed']` | "Запланировать" radio |
| **Date Picker** | `input[placeholder*='ДД.ММ']` | Appears after "Delayed" |
| **Time Picker** | `input[placeholder*='ЧЧ:ММ']` | Appears after "Delayed" |
| **Publish Button** | `button[type='submit']:has-text("Опубликовать")` | |

## 3. Automation Strategy (Python/Playwright)

```python
# Upload Example
page.goto("https://studio.rutube.ru/videos/upload")

# Handle File
with page.expect_file_chooser() as fc_info:
    page.click("button:has-text('Выбрать файл')")
file_chooser = fc_info.value
file_chooser.set_files("my_video.mp4")

# Wait for upload to start (progress bar appears)
page.wait_for_selector(".progress-bar")

# Fill Details
page.fill("input[placeholder='Название видео']", "My Cool Video")
page.fill("textarea", "Uploaded via API Agent")

# Click Save
page.click("button:has-text('Сохранить')")
```

## 4. Edit Thumbnail Flow (After Upload)

This flow is used by `set_thumbnail_playwright.py` after a video has been uploaded.

| Action | Selector / Strategy | Notes |
| :--- | :--- | :--- |
| **Find Video Link** | `a[href*='<video_id>']` | In the main studio list |
| **Edit Cover Button** | `button[aria-label='Редактировать обложку']` | The pencil icon button |
| **File Input (Fallback)** | `input[type='file']` | Used if the edit button isn't present |
| **Upload Menu Item** | `text="Загрузить"` | A dropdown menu item |
| **Crop Modal "Done"**| `button:has-text('Готово')` | Confirms the thumbnail crop |
| **Save Button** | `button:has-text('Сохранить')` | Saves all changes in the edit modal |

