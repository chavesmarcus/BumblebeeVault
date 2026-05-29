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
# This reads the secure digital token you saved inside your Render settings
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") 

class HuntRequest(BaseModel):
    word: str

def execute_precision_hunt(word: str):
    """The background cloud task that searches, snips, and pushes to your GitHub."""
    print(f"🎯 Automated search initiated for word: '{word}'")
    
    # Using your text strategy to lock onto a tight, short video clip clip instantly
    search_query = f"ytsearch1:{word} isolated spoken word movie quote clip"
    
    local_filename = f"temp_{word}.mp3"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'temp_{word}.%(ext)s',
        # Sniper mode: Force the download to only grab the first 2 seconds of the file
        'download_ranges': lambda info_dict, ydl: [{'start_time': 0, 'end_time': 2}],
        'force_keyframes_at_cuts': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        'quiet': True
    }
    
    try:
        # 1. Download the short audio slice to Render's scratch disk
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([search_query])
            
        # 2. Convert the temporary physical file to a GitHub-ready format
        with open(local_filename, "rb") as f:
            encoded_content = base64.b64encode(f.read()).decode("utf-8")
            
        # 3. Use your encrypted token to push it straight to your BumblebeeVault
        github_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/{word}.mp3"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "message": f"🤖 Bumblebee automatic match extraction for: {word}",
            "content": encoded_content
        }
        
        response = requests.put(github_url, headers=headers, json=data)
        print(f"📦 Cloud deployment status for '{word}.mp3': {response.status_code}")
        
    except Exception as e:
        print(f"🌀 Precision hunt failed for '{word}': {e}")
    finally:
        # Clean up the server workspace so it stays lightweight and fast
        if os.path.exists(local_filename):
            os.remove(local_filename)

@app.post("/hunt")
def start_hunting_bounty(request: HuntRequest, background_tasks: BackgroundTasks):
    """Receives the signal from Pythonista and kicks off the hunt in the background."""
    # This background task structure keeps your iPhone from locking up or waiting!
    background_tasks.add_task(execute_precision_hunt, request.word.lower().strip())
    return {"status": "hunting_initialization_successful", "target_word": request.word}
