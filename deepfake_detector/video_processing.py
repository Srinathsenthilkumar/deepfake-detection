import cv2
import os
import urllib.request
import numpy as np

# MediaPipe Tasks API
try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    MEDIAPIPE_AVAILABLE = True
except Exception as e:
    MEDIAPIPE_AVAILABLE = False
    print(f"Notice: MediaPipe import note: {e}")


class VideoProcessor:
    def __init__(self):
        self.detector = None
        self.model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'face_landmarker.task')

        # Download model if missing
        if not os.path.exists(self.model_path):
            print("Downloading MediaPipe Face Landmarker Model...")
            url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
            try:
                urllib.request.urlretrieve(url, self.model_path)
            except Exception as e:
                print(f"Warning: Failed to auto-download Face Landmarker Model: {e}")

        # Initialize detector
        if MEDIAPIPE_AVAILABLE and os.path.exists(self.model_path):
            try:
                base_options = python.BaseOptions(model_asset_path=self.model_path)
                options = vision.FaceLandmarkerOptions(
                    base_options=base_options,
                    output_face_blendshapes=False,
                    output_facial_transformation_matrixes=False,
                    num_faces=1
                )
                self.detector = vision.FaceLandmarker.create_from_options(options)
            except Exception as e:
                print(f"Warning: Could not create FaceLandmarker: {e}")
                self.detector = None

        # Standard landmark indices for eyes and lips (MediaPipe 468 mesh)
        self.LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        self.RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        self.LIPS = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 185, 40, 39, 37, 0, 267, 269, 270, 409]

    def _calculate_ear(self, landmarks, eye_indices):
        """Calculate Eye Aspect Ratio (EAR) to measure eye openness."""
        pts = np.array([(landmarks[i].x, landmarks[i].y) for i in eye_indices])
        width = np.linalg.norm(pts[0] - pts[8])
        height = np.linalg.norm(pts[4] - pts[12])
        return float(height / (width + 1e-6))

    def process_video(self, video_path, max_frames=300):
        """
        Processes video frames to extract biological indicators (blinking & lip dynamics).
        Limits execution to max_frames (~10-15s) to guarantee fast web response.
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

        ear_sequence = []
        lip_sequence = []
        faces_detected = 0
        frames_read = 0

        if not self.detector or not cap.isOpened():
            if cap.isOpened():
                cap.release()
            return {
                'fps': float(fps),
                'lip_sequence': [],
                'blink_variance': 0.0,
                'inconsistency_score': None,
                'has_face': False,
                'error': 'Detector model unavailable or video cannot be opened'
            }

        try:
            while cap.isOpened() and frames_read < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                frames_read += 1

                # Resize if high-res to keep web processing fast & lightweight
                h, w = frame.shape[:2]
                if w > 720:
                    scale = 720.0 / w
                    frame = cv2.resize(frame, (720, int(h * scale)))

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

                results = self.detector.detect(mp_image)

                if results.face_landmarks:
                    faces_detected += 1
                    landmarks = results.face_landmarks[0]

                    # Eye Aspect Ratio
                    left_ear = self._calculate_ear(landmarks, self.LEFT_EYE)
                    right_ear = self._calculate_ear(landmarks, self.RIGHT_EYE)
                    avg_ear = (left_ear + right_ear) / 2.0
                    ear_sequence.append(avg_ear)

                    # Lip vertical spread as movement proxy
                    lip_pts = np.array([(landmarks[i].x, landmarks[i].y) for i in self.LIPS])
                    lip_movement = float(np.std(lip_pts[:, 1]))
                    lip_sequence.append(lip_movement)
                else:
                    if ear_sequence:
                        ear_sequence.append(ear_sequence[-1])
                    else:
                        ear_sequence.append(0.0)
                    lip_sequence.append(0.0)

        finally:
            cap.release()

        # If no face was detected in the video
        if faces_detected < 5:
            return {
                'fps': float(fps),
                'lip_sequence': [],
                'blink_variance': 0.0,
                'inconsistency_score': None,
                'has_face': False,
                'frames_analyzed': frames_read,
                'faces_detected': faces_detected,
                'note': 'No recognizable facial features detected in media'
            }

        # Biological consistency analysis
        # Natural human EAR standard deviation is typically between 0.012 and 0.08
        valid_ears = [e for e in ear_sequence if e > 0.05]
        blink_std = float(np.std(valid_ears)) if valid_ears else 0.0

        if blink_std < 0.006:
            inconsistency_score = 0.88  # Unnaturally rigid (static eyes / face-swap artifact)
        elif blink_std > 0.095:
            inconsistency_score = 0.82  # Unnaturally erratic / jittery
        elif blink_std < 0.012:
            inconsistency_score = 0.55  # Mild suspicion
        else:
            inconsistency_score = 0.12  # Natural physiological range

        return {
            'fps': float(fps),
            'lip_sequence': lip_sequence,
            'blink_variance': round(blink_std, 4),
            'inconsistency_score': round(float(inconsistency_score), 3),
            'has_face': True,
            'frames_analyzed': frames_read,
            'faces_detected': faces_detected
        }
