import librosa
import numpy as np

class AudioProcessor:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate

    def extract_mel_spectrogram(self, audio_path):
        """
        Extracts Mel-spectrogram. 
        Deepfakes synthesized by GANs/TTS often leave acoustic artifacts.
        """
        y, sr = librosa.load(audio_path, sr=self.sample_rate)
        
        # Convert audio waveform to Mel-spectrogram
        mel_spect = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128, fmax=8000)
        
        # Convert power to decibel (log scale) for better feature representation
        mel_spect_db = librosa.power_to_db(mel_spect, ref=np.max)
        return mel_spect_db

    def process_audio(self, audio_path):
        """
        Analyzes audio for synthetic signatures like missing frequencies.
        """
        mel_spect_db = self.extract_mel_spectrogram(audio_path)
        
        # Variance across time per frequency band
        spectral_variance = np.var(mel_spect_db, axis=1) 
        
        # Check high frequency bands (last 32 of 128 bands)
        high_freq_db = np.mean(mel_spect_db[-32:, :])
        low_freq_db = np.mean(mel_spect_db[:32, :])
        
        # Difference in dB
        db_drop = low_freq_db - high_freq_db
        
        # Deepfakes sometimes lack high-freq resolution or have "dead" bands.
        spectral_holes = np.sum(spectral_variance < 5) 
        
        # Synthesized audio often has a sheer drop-off in high frequencies (>35dB drop)
        if db_drop > 35:
             anomaly_score = 0.85
        elif spectral_holes > 15:
             anomaly_score = 0.65
        else:
             anomaly_score = 0.15
        
        return {
            'mel_spectrogram': mel_spect_db,
            'artifact_score': anomaly_score
        }
