import shutil
import os
import sys
import site

def install_patch():
    """
    Kopies the fixed upload.py file from the local patch folder
    to the installed tiktok_uploader library in the current environment.
    """
    # 1. Find the source file (our fixed version)
    source_path = os.path.join(os.path.dirname(__file__), 'tiktok_uploader_patch', 'upload_fixed.py')
    
    if not os.path.exists(source_path):
        print(f"[ERROR] Patch file not found at: {source_path}")
        return

    # 2. Find the destination (site-packages/tiktok_uploader/upload.py)
    # We use site-packages from the current running python interpreter
    site_packages = site.getsitepackages()
    
    target_dir = None
    for sp in site_packages:
        check_path = os.path.join(sp, 'tiktok_uploader')
        if os.path.exists(check_path):
            target_dir = check_path
            break
            
    if not target_dir:
        # Fallback: try to import the module to find its path
        try:
            import tiktok_uploader
            target_dir = os.path.dirname(tiktok_uploader.__file__)
        except ImportError:
            print("[ERROR] tiktok_uploader library is not installed. Run 'pip install -r requirements.txt' first.")
            return

    target_path = os.path.join(target_dir, 'upload.py')

    # 3. Perform the copy
    print(f"[INFO] Installing patch...")
    print(f"   Source: {source_path}")
    print(f"   Target: {target_path}")

    try:
        shutil.copy2(source_path, target_path)
        print(f"[SUCCESS] Patch applied! The uploader is now fixed and ready to use.")
    except Exception as e:
        print(f"[ERROR] Failed to copy file: {e}")

if __name__ == "__main__":
    install_patch()
