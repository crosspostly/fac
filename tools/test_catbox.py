import requests
import os

def upload_to_catbox(file_path):
    print(f"📦 Uploading {file_path} to Catbox...")
    url = "https://catbox.moe/user/api.php"
    try:
        files = {
            'reqtype': (None, 'fileupload'),
            'fileToUpload': open(file_path, 'rb')
        }
        response = requests.post(url, files=files)
        if response.status_code == 200:
            direct_url = response.text.strip()
            print(f"✅ Success: {direct_url}")
            return direct_url
        else:
            print(f"❌ Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

if __name__ == "__main__":
    # Create a dummy file if needed
    if not os.path.exists("test_catbox.txt"):
        with open("test_catbox.txt", "w") as f:
            f.write("Hello Catbox!")
            
    upload_to_catbox("test_catbox.txt")
