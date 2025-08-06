from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import os

from starlette.middleware.cors import CORSMiddleware

from video_transcript_summarization.model.local_type import LocalType
from video_transcript_summarization.utils.utils import clear_intermediate_files

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost:53000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory to save uploaded videos
UPLOAD_DIR = "uploaded_videos"

# Ensure the upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):
    # Validate file content type
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Invalid file type. A video file is required.")

    file_location = os.path.join(UPLOAD_DIR, file.filename)
    try:
        # Write the file to disk
        with open(file_location, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    absolutePath = os.path.abspath(file_location)
    currentType = LocalType(url=absolutePath)

    currentType.fetch_video()
    currentType.get_transcription_text()
    summarization = currentType.summarize_and_elaborate()
    clear_intermediate_files()

    return JSONResponse(status_code=200, content={
        "summarization": summarization
    })

# Install FastAPI and Uvicorn if not already installed:
# pip install fastapi uvicorn python-multipart

# To run the app, use:
# uvicorn app:app --reload --host 0.0.0.0 --port 8000