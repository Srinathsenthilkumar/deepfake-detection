import os
import tempfile
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

# Local modules
from video_processing import VideoProcessor
from audio_processing import AudioProcessor
from multimodal_fusion import FusionEngine
from media_utils import MediaUtils

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'temp_downloads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 # 50 MB max
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

media_utils = MediaUtils(download_dir=app.config['UPLOAD_FOLDER'])
vp = VideoProcessor()
ap = AudioProcessor()
fusion = FusionEngine()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    video_path = None
    audio_path = None
    input_type = request.form.get('input_type')
    
    try:
        # --- Handle File Upload ---
        if input_type == 'file':
            if 'file' not in request.files:
                return jsonify({'error': 'No file part'}), 400
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No selected file'}), 400
            
            filename = secure_filename(file.filename)
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(video_path)
            
        # --- Handle URL Link ---
        elif input_type == 'url':
            url = request.form.get('url')
            if not url:
                return jsonify({'error': 'No URL provided'}), 400
            
            video_path, err_msg = media_utils.download_from_url(url)
            if not video_path:
                return jsonify({'error': f'Failed to download media from URL. Error: {err_msg}'}), 400
                
        else:
            return jsonify({'error': 'Invalid input type'}), 400

        # --- Process Media ---
        # 1. Extract audio if it's a video file
        audio_path = video_path.rsplit('.', 1)[0] + '.wav'
        has_audio = media_utils.extract_audio(video_path, audio_path)
        
        # 2. Analyze Video
        video_results = vp.process_video(video_path)
        
        # 3. Analyze Audio
        if has_audio and os.path.exists(audio_path):
            audio_results = ap.process_audio(audio_path)
        else:
            audio_results = {'mel_spectrogram': [], 'artifact_score': 0.5} # Fallback
            has_audio = False
            
        # 4. Multimodal Fusion
        final_report = fusion.get_final_verdict(video_results, audio_results)
        
        # Add a flag to indicate if we had actual audio to analyze
        final_report['has_audio'] = has_audio

        # Format percentages
        return jsonify({
            'success': True,
            'video_fake_prob': round(final_report['video_fake_prob'] * 100, 1),
            'audio_fake_prob': round(final_report['audio_fake_prob'] * 100, 1),
            'sync_mismatch_prob': round(final_report['sync_mismatch_prob'] * 100, 1),
            'final_fake_prob': round(final_report['final_fake_prob'] * 100, 1)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
    finally:
        # Cleanup temp files
        media_utils.cleanup(video_path, audio_path)

if __name__ == '__main__':
    app.run(debug=True, port=8500)
