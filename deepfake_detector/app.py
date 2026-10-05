import os
import sys
import tempfile
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

# Ensure local directory is in Python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Local modules
from video_processing import VideoProcessor
from audio_processing import AudioProcessor
from multimodal_fusion import FusionEngine
from media_utils import MediaUtils

# Initialize Flask with explicit templates and static directories
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static')
)

app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'temp_downloads')
app.config['MAX_CONTENT_LENGTH'] = 60 * 1024 * 1024  # 60 MB limit
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Lazy/cached processor instantiation
media_utils = MediaUtils(download_dir=app.config['UPLOAD_FOLDER'])
vp = VideoProcessor()
ap = AudioProcessor()
fusion = FusionEngine()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint for web platforms and container orchestrators."""
    return jsonify({
        'status': 'healthy',
        'service': 'deepfake-detector',
        'detector_ready': vp.detector is not None
    }), 200


@app.route('/demo-sample', methods=['POST'])
def demo_sample():
    """Provides immediate simulated forensic data for web demo visitors."""
    sample_type = request.json.get('type', 'synthetic') if request.is_json else request.form.get('type', 'synthetic')
    
    if sample_type == 'synthetic':
        # Simulated face-swap + TTS audio mismatch
        sim_video = {
            'blink_variance': 0.0035,
            'inconsistency_score': 0.88,
            'has_face': True,
            'faces_detected': 120,
            'frames_analyzed': 120,
            'fps': 30.0,
            'lip_sequence': [0.012] * 40
        }
        sim_audio = {
            'has_audio': True,
            'artifact_score': 0.84,
            'spectral_holes': 22,
            'high_low_db_drop': 38.4,
            'mel_spectrogram': None
        }
        verdict = fusion.get_final_verdict(sim_video, sim_audio)
        verdict['sync_mismatch_prob'] = 0.82
        verdict['sync_correlation'] = 0.08
        verdict['final_fake_prob'] = 0.85
        verdict['verdict_title'] = "High Probability Deepfake"
        verdict['verdict_category'] = "danger"
        verdict['explanation'] = (
            "Severe facial landmark rigidity with missing involuntary blinks (<0.005 EAR variance) • "
            "Acoustic frequency cutoffs (>38 dB drop) characteristic of voice cloning • "
            "Desynchronized phoneme-to-lip kinematics"
        )
    else:
        # Simulated authentic live interview
        sim_video = {
            'blink_variance': 0.0342,
            'inconsistency_score': 0.12,
            'has_face': True,
            'faces_detected': 150,
            'frames_analyzed': 150,
            'fps': 30.0,
            'lip_sequence': [0.035] * 50
        }
        sim_audio = {
            'has_audio': True,
            'artifact_score': 0.15,
            'spectral_holes': 3,
            'high_low_db_drop': 18.2,
            'mel_spectrogram': None
        }
        verdict = fusion.get_final_verdict(sim_video, sim_audio)
        verdict['sync_mismatch_prob'] = 0.18
        verdict['sync_correlation'] = 0.76
        verdict['final_fake_prob'] = 0.14
        verdict['verdict_title'] = "Likely Authentic Media"
        verdict['verdict_category'] = "authentic"
        verdict['explanation'] = (
            "Natural biological blinking frequency detected (0.034 EAR variance) • "
            "Broadband harmonic audio resonance with zero synthetic cutoffs • "
            "High temporal alignment between lip shapes and speech cadence"
        )

    return jsonify({
        'success': True,
        'demo': True,
        'final_fake_prob': round(verdict['final_fake_prob'] * 100, 1),
        'video_fake_prob': round((sim_video['inconsistency_score'] or 0.5) * 100, 1),
        'audio_fake_prob': round((sim_audio['artifact_score'] or 0.5) * 100, 1),
        'sync_mismatch_prob': round((verdict.get('sync_mismatch_prob') or 0.5) * 100, 1),
        'verdict_title': verdict['verdict_title'],
        'verdict_category': verdict['verdict_category'],
        'explanation': verdict['explanation'],
        'has_face': True,
        'has_audio': True,
        'details': {
            'blink_variance': sim_video['blink_variance'],
            'faces_detected': sim_video['faces_detected'],
            'spectral_holes': sim_audio['spectral_holes'],
            'high_low_db_drop': sim_audio['high_low_db_drop'],
            'sync_correlation': verdict.get('sync_correlation')
        }
    })


@app.route('/analyze', methods=['POST'])
def analyze():
    media_path = None
    audio_path = None
    input_type = request.form.get('input_type')

    try:
        # --- 1. Ingest Input (File Upload or Web URL) ---
        if input_type == 'file':
            if 'file' not in request.files:
                return jsonify({'error': 'No file attached in request.'}), 400
            file = request.files['file']
            if not file or file.filename == '':
                return jsonify({'error': 'No file selected.'}), 400

            safe_name = secure_filename(file.filename)
            if not safe_name:
                safe_name = "uploaded_media.mp4"
            media_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
            file.save(media_path)

        elif input_type == 'url':
            url = request.form.get('url', '').strip()
            if not url:
                return jsonify({'error': 'Please enter a valid URL.'}), 400

            media_path, err_msg = media_utils.download_from_url(url)
            if not media_path or not os.path.exists(media_path):
                return jsonify({'error': err_msg or 'Failed to download media from the provided URL.'}), 400

        else:
            return jsonify({'error': 'Invalid input type specified.'}), 400

        # --- 2. Modality Routing ---
        is_audio_only = media_utils.is_audio_file(media_path)
        audio_path = os.path.splitext(media_path)[0] + "_extracted.wav"

        # Video Processing
        if is_audio_only:
            video_results = {
                'fps': 0,
                'lip_sequence': [],
                'blink_variance': 0.0,
                'inconsistency_score': None,
                'has_face': False,
                'note': 'Audio-only input'
            }
        else:
            video_results = vp.process_video(media_path, max_frames=300)

        # Audio Extraction & Processing
        has_audio = False
        if is_audio_only:
            has_audio = media_utils.extract_audio(media_path, audio_path)
        else:
            has_audio = media_utils.extract_audio(media_path, audio_path)

        if has_audio and os.path.exists(audio_path):
            audio_results = ap.process_audio(audio_path)
        else:
            audio_results = {
                'mel_spectrogram': None,
                'artifact_score': None,
                'has_audio': False,
                'note': 'No audio track detected'
            }

        # --- 3. Multimodal Fusion Verdict ---
        report = fusion.get_final_verdict(video_results, audio_results)

        # Format percentages safely
        vid_prob = round(report['video_fake_prob'] * 100, 1) if report['video_fake_prob'] is not None else None
        aud_prob = round(report['audio_fake_prob'] * 100, 1) if report['audio_fake_prob'] is not None else None
        sync_prob = round(report['sync_mismatch_prob'] * 100, 1) if report['sync_mismatch_prob'] is not None else None

        return jsonify({
            'success': True,
            'final_fake_prob': round(report['final_fake_prob'] * 100, 1),
            'video_fake_prob': vid_prob,
            'audio_fake_prob': aud_prob,
            'sync_mismatch_prob': sync_prob,
            'verdict_title': report['verdict_title'],
            'verdict_category': report['verdict_category'],
            'explanation': report['explanation'],
            'mode': report['mode'],
            'has_face': video_results.get('has_face', False),
            'has_audio': audio_results.get('has_audio', False),
            'details': {
                'blink_variance': video_results.get('blink_variance'),
                'faces_detected': video_results.get('faces_detected', 0),
                'spectral_holes': audio_results.get('spectral_holes'),
                'high_low_db_drop': audio_results.get('high_low_db_drop'),
                'sync_correlation': report.get('sync_correlation')
            }
        })

    except Exception as e:
        return jsonify({'error': f"Forensic analysis failed: {str(e)}"}), 500

    finally:
        # Guarantee temp files are cleaned up from disk
        media_utils.cleanup(media_path, audio_path)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8500))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    # Bind to 0.0.0.0 for web launch and container compatibility
    app.run(host='0.0.0.0', port=port, debug=debug)
