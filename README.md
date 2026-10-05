# 🛡️ Multimodal AI Deepfake Detection Platform

[![Python](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Vision%20468-0097A7?style=for-the-badge&logo=google&logoColor=white)](https://developers.google.com/mediapipe)
[![Librosa](https://img.shields.io/badge/Librosa-Acoustic%20FFT-FF6F00?style=for-the-badge)](https://librosa.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

An advanced **multimodal digital forensics system** engineered to detect synthetic media, face-swaps, cloned voices, and desynchronized AI speech. 

Combining visual biological indicators, acoustic Mel-spectrogram analysis, and cross-modal lip-phoneme synchronization, this engine identifies subtle inconsistencies invisible to the human eye.

---

## ⚡ Key Capabilities

- **👁️ Biological Eye Blink Dynamics (EAR)**: Analyzes Eye Aspect Ratio (EAR) time-series across 468 facial mesh landmarks to detect unnatural rigidity (<0.005 variance) or erratic jitter common in GAN/diffusion face swaps.
- **🎙️ Acoustic Spectral Forensics**: Computes 128-band Mel-spectrograms via Fourier transform to catch TTS vocoder cliffs (>35 dB drop-off) and synthetic harmonic void holes.
- **🔗 Cross-Modal AV-Synchronization**: Correlates lip aperture kinematics directly with speech energy envelopes to flag dubbed or synthesized speech.
- **🌐 Web Launch Ready**: Fully configured for instant deployment on **Render**, **Railway**, **Hugging Face Spaces**, **Docker**, or **GCP/AWS**.
- **⚡ Instant Demo Testing**: Includes interactive simulated forensics so visitors can test deepfake vs. authentic samples with one click.
- **📊 Exportable Forensic Reports**: Generates downloadable JSON reports containing timestamped forensic evidence.

---

## 🏗️ Multimodal Architecture

```
                    ┌─────────────────────────┐
                    │  Uploaded Media or URL  │
                    └────────────┬────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
       ┌───────────────────┐           ┌───────────────────┐
       │ Video Frame Stream│           │ Audio Wave Stream │
       └─────────┬─────────┘           └─────────┬─────────┘
                 │                               │
                 ▼                               ▼
      [MediaPipe 468 Mesh]             [Librosa 128 Mel-FFT]
      • Eye Aspect Ratio (EAR)         • High-Frequency Drop
      • Involuntary Blink Rate         • Harmonic Voids / Holes
      • Lip Movement Spread            • Vocoder Artifacts
                 │                               │
                 └───────────────┬───────────────┘
                                 │
                                 ▼
                     [Cross-Modal AV-Sync Engine]
                     • Lip Aperture vs. Audio Energy
                     • Pearson Kinematic Correlation
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Multimodal Fusion Score │
                    │ (0% - 100% Probability) │
                    └─────────────────────────┘
```

---

## 🚀 Quick Start (Local Setup)

### 1. Clone the repository
```bash
git clone https://github.com/Srinathsenthilkumar/deepfake-detection.git
cd deepfake-detection
```

### 2. Create a virtual environment
```bash
# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch the application
```bash
python app.py
```
Open **[http://localhost:8500](http://localhost:8500)** in your browser.

---

## 🐳 Docker Deployment

To build and run in a containerized environment with ffmpeg and OpenGL preconfigured:

```bash
# Build Docker image
docker build -t deepfake-detector .

# Run container
docker run -p 8500:8500 -e PORT=8500 deepfake-detector
```
Or with Docker Compose:
```bash
docker compose up -d
```

---

## ☁️ Cloud Web Launch (Render / Railway / Hugging Face)

### Deploy on Render
1. Create a free account at [render.com](https://render.com).
2. Click **New +** → **Web Service** → Connect your GitHub repository.
3. Configuration:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 app:app`
   - **Health Check Path**: `/health`
*(Alternatively, use the included `render.yaml` for 1-click Blueprint deployment).*

### Deploy on Railway / Heroku
- The repository includes a `Procfile`:
  ```
  web: gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 app:app
  ```
  Railway and Heroku automatically detect the `Procfile` and `$PORT` variable.

---

## 📡 REST API Reference

### 1. Ingest & Analyze Media
- **Endpoint**: `POST /analyze`
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `input_type`: `'file'` or `'url'`
  - `file`: Media file (`.mp4`, `.webm`, `.mov`, `.wav`, `.mp3`)
  - `url`: Public media link (e.g. YouTube video)
- **Response**:
  ```json
  {
    "success": true,
    "final_fake_prob": 85.0,
    "video_fake_prob": 88.0,
    "audio_fake_prob": 84.0,
    "sync_mismatch_prob": 82.0,
    "verdict_title": "High Probability Deepfake",
    "verdict_category": "danger",
    "explanation": "Severe facial landmark rigidity with missing involuntary blinks...",
    "has_face": true,
    "has_audio": true,
    "details": {
      "blink_variance": 0.0035,
      "faces_detected": 120,
      "spectral_holes": 22,
      "high_low_db_drop": 38.4,
      "sync_correlation": 0.08
    }
  }
  ```

### 2. Instant Demo Testing
- **Endpoint**: `POST /demo-sample`
- **Payload**: `{"type": "synthetic"}` or `{"type": "authentic"}`
- **Response**: Immediate simulated biometric breakdown for live demos.

### 3. Service Health Check
- **Endpoint**: `GET /health`
- **Response**: `{"status": "healthy", "service": "deepfake-detector", "detector_ready": true}`

---

## 📂 Project Structure

```
deepfake-detection/
├── app.py                      # Root production entrypoint
├── requirements.txt            # Root dependencies with Gunicorn & OpenCV-headless
├── Procfile                    # Web service process configuration
├── Dockerfile                  # Container definition with ffmpeg runtime
├── docker-compose.yml          # Local container compose configuration
├── render.yaml                 # Render Blueprint specification
├── .dockerignore               # Container build exclusions
├── .gitignore                  # Git tracking rules
├── README.md                   # Project documentation
└── deepfake_detector/
    ├── app.py                  # Core Flask server & API routes
    ├── video_processing.py     # MediaPipe FaceLandmarker EAR & blink variance
    ├── audio_processing.py     # Librosa 128-band Mel-spectrogram analysis
    ├── multimodal_fusion.py    # Cross-modal AV-sync & weighted ensemble
    ├── media_utils.py          # yt-dlp & multi-strategy audio extraction
    ├── face_landmarker.task    # Google MediaPipe biometric model
    ├── static/
    │   ├── app.js              # Live player preview, multi-phase scanner, JSON export
    │   └── style.css           # Glassmorphism, cybersecurity aesthetic & responsive grid
    └── templates/
        └── index.html          # Semantic HTML5 UI layout
```

---

## 📜 License
This project is open-source and intended for academic research and synthetic media forensics.
