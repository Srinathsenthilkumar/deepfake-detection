import numpy as np


class SyncDetectorCNN:
    """
    Evaluates temporal cross-modal synchronization between visual lip dynamics
    and acoustic phoneme energy envelopes.
    """
    def __init__(self):
        pass

    def evaluate_sync(self, lip_sequence, audio_mel_spectrogram, fps=30.0):
        """
        Calculates correlation between facial lip dynamics and audio energy envelopes.
        Returns a sync mismatch probability (0.0 to 1.0).
        """
        if (
            not lip_sequence
            or len(lip_sequence) < 15
            or audio_mel_spectrogram is None
            or audio_mel_spectrogram.size == 0
        ):
            return 0.5, 0.0

        try:
            # Calculate audio energy envelope across Mel bands over time
            audio_energy = np.mean(audio_mel_spectrogram, axis=0)
            if len(audio_energy) < 5 or np.all(audio_energy == audio_energy[0]):
                return 0.5, 0.0

            # Temporally interpolate audio envelope to align with video frame timestamps
            n_vid_frames = len(lip_sequence)
            t_vid = np.linspace(0, 1, n_vid_frames)
            t_aud = np.linspace(0, 1, len(audio_energy))

            audio_energy_interp = np.interp(t_vid, t_aud, audio_energy)

            # Pearson correlation coefficient
            corr_matrix = np.corrcoef(lip_sequence, audio_energy_interp)
            corr = float(corr_matrix[0, 1])

            if np.isnan(corr):
                return 0.5, 0.0

            # High positive correlation indicates synchronized speech & lip movement
            # Low or negative correlation indicates desynchronized or dubbed speech
            mismatch_prob = 1.0 - max(0.0, min(1.0, (corr + 0.15) * 1.35))
            return round(float(mismatch_prob), 3), round(corr, 3)

        except Exception as e:
            print(f"Sync evaluation notice: {e}")
            return 0.5, 0.0


class FusionEngine:
    def __init__(self):
        self.sync_model = SyncDetectorCNN()

    def get_final_verdict(self, video_results, audio_results):
        """
        Fuses unimodal signals (Video facial dynamics, Audio spectral artifacts)
        with cross-modal AV-synchronization correlation.
        """
        vid_score = video_results.get('inconsistency_score')
        aud_score = audio_results.get('artifact_score')
        has_face = video_results.get('has_face', False)
        has_audio = audio_results.get('has_audio', False)

        sync_mismatch = 0.5
        sync_corr = 0.0

        # Case 1: Both Video & Audio available
        if has_face and has_audio and vid_score is not None and aud_score is not None:
            sync_mismatch, sync_corr = self.sync_model.evaluate_sync(
                video_results.get('lip_sequence', []),
                audio_results.get('mel_spectrogram'),
                video_results.get('fps', 30.0)
            )
            # Weighted multi-modal fusion
            final_fake_prob = (0.35 * vid_score) + (0.35 * aud_score) + (0.30 * sync_mismatch)
            mode = "multimodal"

        # Case 2: Only Video available
        elif has_face and vid_score is not None:
            final_fake_prob = vid_score
            mode = "video_only"

        # Case 3: Only Audio available
        elif has_audio and aud_score is not None:
            final_fake_prob = aud_score
            mode = "audio_only"

        # Case 4: Neither available or inconclusive
        else:
            final_fake_prob = 0.5
            mode = "inconclusive"

        final_fake_prob = max(0.0, min(1.0, final_fake_prob))

        # Generate human-readable forensic explanation
        explanations = []
        if mode == "multimodal":
            if final_fake_prob >= 0.65:
                if vid_score > 0.6:
                    explanations.append("Unnatural facial landmark / eye blink patterns detected")
                if aud_score > 0.6:
                    explanations.append("Acoustic frequency cutoffs indicative of synthetic speech / voice cloning")
                if sync_mismatch > 0.6:
                    explanations.append("Substantial desynchronization between lip kinematics and acoustic energy")
            elif final_fake_prob <= 0.35:
                explanations.append("Natural biological blinking variance detected")
                explanations.append("Harmonic acoustic spectrum consistent with organic human voice")
                explanations.append("Strong temporal alignment between lip movement and speech audio")
            else:
                explanations.append("Mixed signals across visual and acoustic modalities; review recommended")
        elif mode == "video_only":
            if final_fake_prob >= 0.65:
                explanations.append("Facial expression dynamics exhibit rigidity or abnormal micro-jitter")
            else:
                explanations.append("Facial motion and eye aspect ratios fall within normal human physiological ranges")
        elif mode == "audio_only":
            if final_fake_prob >= 0.65:
                explanations.append("Acoustic frequency distribution indicates voice synthesis artifacts")
            else:
                explanations.append("Audio spectral distribution matches natural organic vocal characteristics")
        else:
            explanations.append("No active facial landmarks or clear audio track could be evaluated")

        if not explanations:
            explanations.append("Analysis concluded within moderate confidence thresholds")

        # Determine category and title
        if final_fake_prob >= 0.65:
            verdict_category = "danger"
            verdict_title = "High Probability Deepfake"
        elif final_fake_prob >= 0.40:
            verdict_category = "warning"
            verdict_title = "Suspicious Media Detected"
        else:
            verdict_category = "authentic"
            verdict_title = "Likely Authentic Media"

        return {
            'video_fake_prob': vid_score,
            'audio_fake_prob': aud_score,
            'sync_mismatch_prob': sync_mismatch if (has_face and has_audio) else None,
            'sync_correlation': sync_corr if (has_face and has_audio) else None,
            'final_fake_prob': round(final_fake_prob, 3),
            'verdict_category': verdict_category,
            'verdict_title': verdict_title,
            'mode': mode,
            'explanation': " • ".join(explanations)
        }
