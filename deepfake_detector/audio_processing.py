import librosa
import numpy as np
import os


class AudioProcessor:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate

    def extract_mel_spectrogram(self, audio_path, max_duration=30.0):
        """
        Extracts Mel-spectrogram from an audio file.
        Caps duration to max_duration (default 30s) to guarantee fast web response.
        """
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 100:
            return None

        try:
            # Load up to max_duration seconds
            y, sr = librosa.load(audio_path, sr=self.sample_rate, duration=max_duration)
            if y is None or len(y) < self.sample_rate * 0.2:  # Less than 200ms
                return None

            # Convert audio waveform to Mel-spectrogram
            mel_spect = librosa.feature.melspectrogram(
                y=y,
                sr=sr,
                n_mels=128,
                fmax=8000,
                hop_length=512
            )

            # Convert power to decibel (log scale)
            mel_spect_db = librosa.power_to_db(mel_spect, ref=np.max)
            return mel_spect_db
        except Exception as e:
            print(f"Error extracting Mel-spectrogram: {e}")
            return None

    def process_audio(self, audio_path):
        """
        Analyzes audio for synthetic signatures (TTS artifacts, cutoffs, spectral holes).
        """
        mel_spect_db = self.extract_mel_spectrogram(audio_path)
        if mel_spect_db is None or mel_spect_db.shape[1] == 0:
            return {
                'mel_spectrogram': None,
                'artifact_score': None,
                'has_audio': False,
                'note': 'No valid audio track found'
            }

        # Variance across time per frequency band
        spectral_variance = np.var(mel_spect_db, axis=1)

        # High vs low frequency band analysis (last 32 vs first 32 of 128 bands)
        high_freq_db = float(np.mean(mel_spect_db[-32:, :]))
        low_freq_db = float(np.mean(mel_spect_db[:32, :]))
        db_drop = float(low_freq_db - high_freq_db)

        # Spectral holes: synthesized TTS models often leave unnatural silence in upper registers
        spectral_holes = int(np.sum(spectral_variance < 5.0))

        # Synthetic TTS and voice clone detection logic
        if db_drop > 36.0:
            anomaly_score = 0.86  # Extreme high-frequency cut-off typical of vocoders
        elif spectral_holes > 18:
            anomaly_score = 0.72  # Unnatural harmonic voids
        elif db_drop > 28.0 or spectral_holes > 10:
            anomaly_score = 0.48  # Moderate acoustic artifacts
        else:
            anomaly_score = 0.14  # Natural acoustic spectrum

        return {
            'mel_spectrogram': mel_spect_db,
            'artifact_score': round(float(anomaly_score), 3),
            'high_low_db_drop': round(db_drop, 2),
            'spectral_holes': spectral_holes,
            'has_audio': True
        }
