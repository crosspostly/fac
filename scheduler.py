import time
import subprocess
import datetime
import os
import sys

# Configuration
INTERVAL_HOURS = 3
INTERVAL_SECONDS = INTERVAL_HOURS * 3600

def log(msg):
    print(f"[{datetime.datetime.now()}] {msg}")

# ...

def run_upload():
    log("🚀 Starting scheduled YOUTUBE -> RUTUBE sync job...")
    try:
        # Запускаем скрипт синхронизации
        script_path = os.path.join(os.path.dirname(__file__), "sync_production.py")
        
        # Use venv python if available
        venv_python = os.path.join(os.path.dirname(__file__), "venv", "bin", "python")
        if os.path.exists(venv_python):
            executable = venv_python
        else:
            executable = sys.executable

        result = subprocess.run(
            [executable, script_path],
            capture_output=True,
            text=True
        )
        
        # Log output
        print("--- Upload Output ---")
        print(result.stdout)
        if result.stderr:
            print("--- Upload Errors ---")
            print(result.stderr)
            
        if result.returncode == 0:
            log("✅ Upload job finished successfully.")
        else:
            log("❌ Upload job failed.")
            
    except Exception as e:
        log(f"❌ Exception during upload execution: {e}")

def main():
    log(f"📅 Scheduler started. Will run every {INTERVAL_HOURS} hours.")
    
    while True:
        run_upload()
        
        log(f"💤 Sleeping for {INTERVAL_HOURS} hours...")
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
