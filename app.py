import ollama
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import os
import aiofiles

from starlette.middleware.cors import CORSMiddleware

from video_transcript_summarization.model.local_type import LocalType
from video_transcript_summarization.model.youtube_video_request import YoutubeVideoRequest
from video_transcript_summarization.utils.env_helper import load_environment_config
from video_transcript_summarization.utils.utils import clear_intermediate_files

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost:53000", "http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory to save uploaded videos
UPLOAD_DIR = "uploaded_videos"

# Ensure the upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/summarize-local-video")
async def summarize_local_video(file: UploadFile = File(...), target_language: str = File("auto")):
    # Validate file content type
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Invalid file type. A video file is required.")

    file_location = os.path.join(UPLOAD_DIR, file.filename)
    # Write the file to disk
    try:
        async with aiofiles.open(file_location, "wb") as buffer:
            content = await file.read()
            await buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to handle with file: {e}")

    absolute_path = os.path.abspath(file_location)

    current_type = LocalType(url=absolute_path)
    load_environment_config(current_type)
    current_type.target_language = target_language

    current_type.fetch_video()
    current_type.get_transcription_text()
    summarization = current_type.summarize_and_elaborate()
    clear_intermediate_files()

    return JSONResponse(status_code=200, content={
        "summarization": summarization
    })


@app.post("/summarize-local-video-with-config")
async def summarize_local_video_with_config(
        file: UploadFile = File(...),
        target_language: str = "auto",
        ollama_host_client: str = None,
        llm: str = None,
        max_output_tokens: int = None,
):
    # Validate file content type
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Invalid file type. A video file is required.")

    file_location = os.path.join(UPLOAD_DIR, file.filename)
    try:
        # Write the file to disk
        async with aiofiles.open(file_location, "wb") as buffer:
            content = await file.read()
            await buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to handle with file: {e}")

    absolute_path = os.path.abspath(file_location)

    current_type = LocalType(url=absolute_path)
    load_environment_config(current_type)
    current_type.target_language = target_language

    if llm:
        current_type.model = llm

    if max_output_tokens:
        current_type.max_output_tokens = max_output_tokens

    if ollama_host_client:
        current_type.ollama_client = ollama.Client(
            host=ollama_host_client,
            verify=False
        )

    current_type.fetch_video()
    current_type.get_transcription_text()
    summarization = current_type.summarize_and_elaborate()
    clear_intermediate_files()

    return JSONResponse(status_code=200, content={
        "summarization": summarization
    })


@app.post("/summarize-youtube-video")
async def summarize_youtube_video(request: YoutubeVideoRequest):
    if not request.url:
        raise HTTPException(status_code=400, detail="YouTube video URL is required.")

    current_type = request.to_youtube_type()

    current_type.fetch_video()
    current_type.get_transcription_text()
    summarization = current_type.summarize_and_elaborate()
    clear_intermediate_files()

    return JSONResponse(status_code=200, content={
        "summarization": summarization
    })

# To run the app, use:
# uvicorn app:app --reload --host 0.0.0.0 --port 8000
