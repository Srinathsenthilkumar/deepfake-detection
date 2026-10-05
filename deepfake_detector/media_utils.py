import os
import shutil
import subprocess
import yt_dlp

# Safe MoviePy import across both v1.x and v2.x
try:
    from moviepy import VideoFileClip
except ImportError:
    try:
        from moviepy.editor import VideoFileClip
    except ImportError:
        VideoFileClip = None

# Safe imageio-ffmpeg discovery
try:
    import imageio_ffmpeg
    FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG_BIN = "ffmpeg"


class MediaUtils:
    def __init__(self, download_dir=None):
        if download_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.download_dir = os.path.join(base_dir, "temp_downloads")
        else:
            self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)

    def is_audio_file(self, file_path):
        """Checks if the file extension is primarily audio."""
        audio_exts = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".wma"}
        _, ext = os.path.splitext(file_path.lower())
        return ext in audio_exts

    def extract_audio(self, media_path, audio_path):
        """
        Extracts mono 16kHz PCM WAV audio from a video or audio file.
        Uses MoviePy with fallback to imageio-ffmpeg/system ffmpeg.
        """
        if not os.path.exists(media_path):
            return False

        # If already a WAV file, make a copy or normalize
        if media_path.lower().endswith(".wav"):
            try:
                shutil.copyfile(media_path, audio_path)
                return True
            except Exception:
                pass

        # Strategy 1: FFMPEG CLI via imageio-ffmpeg or system binary
        if FFMPEG_BIN:
            try:
                cmd = [
                    FFMPEG_BIN,
                    "-y",
                    "-i", media_path,
                    "-vn",
                    "-acodec", "pcm_s16le",
                    "-ar", "16000",
                    "-ac", "1",
                    audio_path
                ]
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    timeout=45
                )
                if result.returncode == 0 and os.path.exists(audio_path) and os.path.getsize(audio_path) > 100:
                    return True
            except Exception as e:
                print(f"FFmpeg extract notice: {e}")

        # Strategy 2: MoviePy VideoFileClip
        if VideoFileClip is not None:
            try:
                video = VideoFileClip(media_path)
                if video.audio is None:
                    video.close()
                    return False

                video.audio.write_audiofile(
                    audio_path,
                    codec="pcm_s16le",
                    fps=16000,
                    nbytes=2,
                    ffmpeg_params=["-ac", "1"],
                    verbose=False,
                    logger=None
                )
                video.close()
                return os.path.exists(audio_path) and os.path.getsize(audio_path) > 100
            except Exception as e:
                print(f"MoviePy Extract Error: {e}")

        return False

    def download_from_url(self, url):
        """Downloads video/audio from supported web URLs (YouTube, Vimeo, direct media, etc.)."""
        output_template = os.path.join(self.download_dir, "%(id)s.%(ext)s")
        ydl_opts = {
            "format": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]/best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "max_filesize": 50 * 1024 * 1024,  # 50 MB limit
            "socket_timeout": 30,
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            },
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web"]
                }
            },
            "extract_flat": False
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    return None, "Could not extract media info from URL."

                download_path = ydl.prepare_filename(info)
                if not os.path.exists(download_path):
                    base_path = download_path.rsplit(".", 1)[0]
                    for ext in [".mp4", ".webm", ".mkv", ".m4a", ".mp3"]:
                        candidate = base_path + ext
                        if os.path.exists(candidate):
                            return candidate, None
                return download_path, None
        except Exception as e:
            err_str = str(e)
            print(f"Error downloading: {err_str}", flush=True)
            if "Unsupported URL" in err_str:
                return None, "Provided URL is not supported or direct stream is inaccessible."
            if "Sign in to confirm" in err_str or "bot" in err_str.lower():
                return None, "Platform requested bot verification. Please download the video and upload the file directly."
            return None, f"Failed to download media: {err_str}"

    def cleanup(self, *file_paths):
        """Removes temporary files safely without throwing exceptions."""
        for path in file_paths:
            if path and isinstance(path, str) and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"Notice: Could not delete temporary file {path}: {e}")
