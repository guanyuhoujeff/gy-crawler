
import os
import yt_dlp
import sys

# Ensure site-packages are in path
sys.path.append("/home/barai/.local/lib/python3.12/site-packages")

PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLnaQkVsMNAvCFj1C7C_NJEimhvS1-DUVN"
DOWNLOAD_DIR = "downloads"

def download_videos(playlist_url, limit=10):
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    print(f"Downloading top {limit} videos from playlist: {playlist_url}")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(upload_date)s_%(title)s.%(ext)s'),
        'quiet': False,
        'ignoreerrors': True,
        'playlist_items': f'1-{limit}', # Download first 10 items directly
        'sleep_interval': 1, # Polite delay
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([playlist_url])
        
    print("Download process finished.")

if __name__ == "__main__":
    download_videos(PLAYLIST_URL)