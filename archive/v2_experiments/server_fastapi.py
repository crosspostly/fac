import os
import shutil
import datetime
from typing import Annotated
from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, HTTPException
from rutube.rutube_uploader import schedule_upload_task

app = FastAPI()

TEMP_DIR = "rutube/temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

@app.post("/videos/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    video_file: Annotated[UploadFile, File()],
    title: Annotated[str, Form()],
    description: Annotated[str, Form()],
    publish_date: Annotated[str, Form()] # Expecting ISO format or similar string
):
    """
    Endpoint to receive video and schedule upload to Rutube.
    Payload: multipart/form-data
    """
    
    # 1. Validation
    if not video_file.filename.endswith(('.mp4', '.mov', '.avi', '.mkv')):
        raise HTTPException(status_code=400, detail="Invalid file format. Allowed: mp4, mov, avi, mkv")

    try:
        dt = datetime.datetime.fromisoformat(publish_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid publish_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")

    if dt < datetime.datetime.now():
         raise HTTPException(status_code=400, detail="Publish date must be in the future")

    # 2. Save file temporarily
    file_path = os.path.join(TEMP_DIR, f"{int(datetime.datetime.now().timestamp())}_{video_file.filename}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(video_file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # 3. Trigger background task
    # Note: running blocking playwright code in background_tasks works in FastAPI 
    # but strictly speaking should be run in a threadpool if it blocks the event loop.
    # Since playwright sync api blocks, we should be careful. 
    # For this prototype, standard BackgroundTasks runs in a threadpool so it's okay.
    
    background_tasks.add_task(run_upload_process, file_path, title, description, dt)

    return {
        "status": "queued",
        "message": f"Video '{title}' scheduled for {publish_date}",
        "file_saved_at": file_path
    }

def run_upload_process(file_path, title, description, publish_date):
    """
    Wrapper to run the uploader and clean up file.
    """
    print(f"Background task started for {file_path}")
    success, msg = schedule_upload_task(file_path, title, description, publish_date)
    
    if success:
        print(f"✅ Upload task completed: {msg}")
    else:
        print(f"❌ Upload task failed: {msg}")
    
    # Clean up temp file
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Temp file removed: {file_path}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
