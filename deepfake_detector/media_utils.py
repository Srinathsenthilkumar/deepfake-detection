import os
import subprocess
import tempfile
import yt_dlp
from moviepy import VideoFileClip

class MediaUtils:
    def __init__(self, download_dir="temp_downloads"):
        self.download_dir = download_dir
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

    def extract_audio(self, video_path, audio_path):
        """Extracts audio from a video file using moviepy to avoid ffmpeg PATH errors."""
        try:
            # We use moviepy here so the user doesn't need to manually install ffmpeg
            # on their Windows machine and add it to their system PATH
            video = VideoFileClip(video_path)
            if video.audio is None:
                video.close()
                return False
                
            video.audio.write_audiofile(audio_path, codec='pcm_s16le', verbose=False, logger=None)
            video.close()
            return True
        except Exception as e:
            print(f"MoviePy Extract Error: {e}")
            return False

    def download_from_url(self, url):
        """Downloads the best quality video/audio from a URL using yt-dlp."""
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': os.path.join(self.download_dir, '%(id)s.%(ext)s'),
            'quiet': False,
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            },
            'extract_flat': False
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                download_path = ydl.prepare_filename(info)
                # yt-dlp might change the extension after merging
                if not os.path.exists(download_path):
                    # Try checking for .mkv or .webm if .mp4 failed during merge
                    base_path = download_path.rsplit('.', 1)[0]
                    for ext in ['.mp4', '.webm', '.mkv']:
                        if os.path.exists(base_path + ext):
                            return base_path + ext, None
                return download_path, None
        except Exception as e:
            print(f"Error downloading: {e}", flush=True)
            return None, str(e)

    def cleanup(self, *file_paths):
        """Removes temporary files."""
        for path in file_paths:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"Error deleting {path}: {e}")
