import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import cloudinary
import cloudinary.uploader
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Milla Core API")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuration ---
# Ensure these are set in your Render/Local environment variables
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID")

# Init Cloudinary
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

# --- Data Models ---
class VideoRequest(BaseModel):
    url: str
    language: str = "he"

# --- Helper Functions ---

def download_audio_from_youtube(url):
    """Downloads audio from YouTube link using yt-dlp"""
    timestamp = int(time.time())
    filename = f"temp_audio_{timestamp}"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}],
        'outtmpl': filename,
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(f"Error downloading YouTube: {e}")
        return None
        
    return f"{filename}.mp3"

def safe_extract_text(data):
    """Recursively extracts text from diverse RunPod JSON responses"""
    extracted_text = ""
    
    if isinstance(data, dict):
        if "text" in data and isinstance(data["text"], str):
            extracted_text += data["text"] + " "
        
        for key in ["segments", "result", "output"]:
            if key in data:
                extracted_text += safe_extract_text(data[key])
                
    elif isinstance(data, list):
        for item in data:
            extracted_text += safe_extract_text(item)
            
    return extracted_text

# --- Endpoints ---

@app.get("/")
def home():
    """Health check endpoint"""
    return {"status": "alive", "message": "Milla Core API is running"}

@app.post("/transcribe")
async def transcribe_video(request: VideoRequest):
    """
    Main transcription flow:
    1. Handle YouTube DL or direct link.
    2. Upload to Cloudinary (if local).
    3. Send to RunPod (Ivrit.ai model).
    4. Parse result.
    """
    local_file = None
    try:
        print(f"Processing URL: {request.url}")
        
        # Handle YouTube vs Direct Link
        if "youtube.com" in request.url or "youtu.be" in request.url:
            local_file = download_audio_from_youtube(request.url)
            if not local_file:
                return {"status": "error", "message": "Failed to download from YouTube"}
                
            upload_result = cloudinary.uploader.upload(local_file, resource_type="video")
            public_url = upload_result['secure_url']
        else:
            public_url = request.url

        # Prepare RunPod request
        headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}", "Content-Type": "application/json"}
        
        payload = {
            "input": {
                "model": "ivrit-ai/whisper-large-v3-turbo-ct2", 
                "transcribe_args": {
                    "url": public_url, 
                    "language": request.language,
                    "return_timestamps": True,
                    "diarize": False
                }
            }
        }
        
        # Send to RunPod (Sync)
        print("Sending to RunPod...")
        response = requests.post(f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/runsync", json=payload, headers=headers)
        
        if response.status_code != 200: 
            return {"status": "error", "message": f"RunPod Error: {response.text}"}

        raw_data = response.json()
        print(f"DEBUG RAW RESPONSE: {raw_data}") 

        # Extract Text
        final_text = ""
        if "output" in raw_data:
            final_text = safe_extract_text(raw_data["output"]).strip()
        
        # Cleanup
        if local_file and os.path.exists(local_file): 
            os.remove(local_file)
        
        if not final_text:
             return {"status": "success_empty", "message": "No text found", "debug_raw": raw_data}

        return {
            "status": "success", 
            "transcription": final_text, 
            "audio_url": public_url
        }

    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        if local_file and os.path.exists(local_file): 
            os.remove(local_file)
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
