import os
import base64
import requests
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from yt_dlp import YoutubeDL
import imageio_ffmpeg

app = FastAPI()

# --- STANDALONE FFMPEG INJECTION ---
# This pulls the standalone binary path directly from our Python module,
# bypassing the Render system blocks completely!
FFMPEG_BINARY = imageio_ffmpeg.get_ffmpeg_exe()

# --- TARGET CONFIGURATION ---
GITHUB_USERNAME = "chavesmarcus"
REPO_NAME = "BumblebeeVault"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") 

class HuntRequest(BaseModel):
    word: str

def execute_precision_hunt(word: str):
    print(f"🎯 Pop-culture search initiated for: '{word}'")
    local_filename = f"temp_{word}.mp3"
    
    search_query = f"ytsearch1:{word} movie quote clip audio scene"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'temp_{word}.%(ext)s',
        
        # Tell yt-dlp exactly where our standalone binary is hiding
        'ffmpeg_location': FFMPEG_BINARY,
        
        'match_filter': lambda info, *, incomplete: \
            'Video too long' if info.get('duration') and info.get('duration') > 15 else None,
            
        'download_ranges': lambda info_dict, ydl: [{'start_time': 0, 'end_time': 1.5}],
        'force_keyframes_at_cuts': True,
        
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        'quiet': True,
        'no_warnings': True
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([search_query])
            
        with open(local_filename, "rb") as f:
            video_audio_bytes = f.read()
            
        github_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/{word}.mp3"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "message": f"🎬 Bumblebee pop-culture clip audio extraction: {word}",
            "content": base64.b64encode(video_audio_bytes).decode("utf-8")
        }
        
        repo_check = requests.get(github_url, headers=headers)
        if repo_check.status_code == 200:
            data["sha"] = repo_check.json().get("sha")
            
        response = requests.put(github_url, headers=headers, json=data)
        print(f"📦 Cloud vault sync status for '{word}.mp3': {response.status_code}")
        
    except Exception as e:
        print(f"🌀 Pop-culture hunt pipeline failed: {e}")
    finally:
        if os.path.exists(local_filename):
            os.remove(local_filename)

@app.post("/hunt")
def start_hunting_bounty(request: HuntRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(execute_precision_hunt, request.word.lower().strip())
    return {"status": "hunting_initialization_successful", "target_word": request.word}
