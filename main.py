import os
import base64
import requests
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from yt_dlp import YoutubeDL

app = FastAPI()

# --- TARGET CONFIGURATION ---
GITHUB_USERNAME = "chavesmarcus"
REPO_NAME = "BumblebeeVault"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") 

class HuntRequest(BaseModel):
    word: str

def execute_precision_hunt(word: str):
    print(f"🎯 Pop-culture search initiated for: '{word}'")
    local_filename = f"temp_{word}.mp3"
    
    # POP-CULTURE ARCHIVE STRATEGY:
    # We alter the search string to specifically target short movie quotes, 
    # movie clip archives, and brief cultural audio bites.
    search_query = f"ytsearch1:{word} movie quote clip audio scene"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'temp_{word}.%(ext)s',
        
        # AGGRESSIVE SERVER LIMITS: 
        # This tells the server to completely drop the connection if the video is longer 
        # than 15 seconds. This keeps our free cloud worker from running out of memory!
        'match_filter': lambda info, *, incomplete: \
            'Video too long' if info.get('duration') and info.get('duration') > 15 else None,
            
        # Grab just the punchiest 1.5-second snippet right from the clip
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
        # 1. Snipe the pop-culture file to the cloud scratch disk
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([search_query])
            
        # 2. Convert to transmission data bytes
        with open(local_filename, "rb") as f:
            video_audio_bytes = f.read()
            
        # 3. Securely deploy directly to your BumblebeeVault
        github_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/{word}.mp3"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "message": f"🎬 Bumblebee automatic audio-clip extraction for: {word}",
            "content": base64.b64encode(video_audio_bytes).decode("utf-8")
        }
        
        # If file already exists, grab its SHA to allow overwrite updates
        repo_check = requests.get(github_url, headers=headers)
        if repo_check.status_code == 200:
            data["sha"] = repo_check.json().get("sha")
            
        response = requests.put(github_url, headers=headers, json=data)
        print(f"📦 Cloud vault sync status for '{word}.mp3': {response.status_code}")
        
    except Exception as e:
        print(f"🌀 Pop-culture hunt pipeline bypassed or failed: {e}")
    finally:
        if os.path.exists(local_filename):
            os.remove(local_filename)

@app.post("/hunt")
def start_hunting_bounty(request: HuntRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(execute_precision_hunt, request.word.lower().strip())
    return {"status": "hunting_initialization_successful", "target_word": request.word}
