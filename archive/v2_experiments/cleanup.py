import shutil
import os

files_to_move = ['check_status.py', 'check_ids.py', 'fix_upload.py', 'test_yt_upload.py', 'test_video.mp4']
archive_dir = 'archive'

if not os.path.exists(archive_dir):
    os.makedirs(archive_dir)

for f in files_to_move:
    if os.path.exists(f):
        try:
            shutil.move(f, os.path.join(archive_dir, f))
            print(f"Moved {f}")
        except Exception as e:
            print(f"Error moving {f}: {e}")
    else:
        print(f"Skipped {f} (not found)")
