import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import urllib.request
import os

class VideoProcessor:
    def __init__(self):
        # Setup FaceLandmarker with the Tasks API
        self.model_path = os.path.join(os.path.dirname(__file__), 'face_landmarker.task')
        if not os.path.exists(self.model_path):
            print("Downloading Face Landmarker Model...")
            url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
            try:
                urllib.request.urlretrieve(url, self.model_path)
            except Exception as e:
                print(f"Failed to download MediaPipe Model: {e}")

        if os.path.exists(self.model_path):
            base_options = python.BaseOptions(model_asset_path=self.model_path)
            options = vision.FaceLandmarkerOptions(base_options=base_options,
                                                   output_face_blendshapes=False,
                                                   output_facial_transformation_matrixes=False,
                                                   num_faces=1)
            self.detector = vision.FaceLandmarker.create_from_options(options)
        else:
            self.detector = None
            
        # Standard landmarks for eyes and lips
        self.LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        self.RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        self.LIPS = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291]

    def _calculate_ear(self, landmarks, eye_indices):
        """Calculate Eye Aspect Ratio (EAR) to measure how open the eye is."""
        pts = np.array([(landmarks[i].x, landmarks[i].y) for i in eye_indices])
        width = np.linalg.norm(pts[0] - pts[8]) # Rough horizontal distance
        height = np.linalg.norm(pts[4] - pts[12]) # Rough vertical distance
        return height / (width + 1e-6)

    def process_video(self, video_path):
        """
        Iterates over video frames and calculates facial metrics over time.
        """
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        ear_sequence = []
        lip_sequence = []
        
        if not self.detector:
             return {
                'fps': fps or 30.0,
                'lip_sequence': [],
                'blink_variance': 0,
                'inconsistency_score': 0.5
            }
            
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            # OpenCV captures in BGR, MediaPipe Tasks needs MP Image
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            
            results = self.detector.detect(mp_image)
            
            if results.face_landmarks:
                landmarks = results.face_landmarks[0]
                
                # Extract Eye Aspect Ratio for blink detection
                left_ear = self._calculate_ear(landmarks, self.LEFT_EYE)
                right_ear = self._calculate_ear(landmarks, self.RIGHT_EYE)
                avg_ear = (left_ear + right_ear) / 2.0
                ear_sequence.append(avg_ear)
                
                # Extract Lip features (vertical spread as movement proxy)
                lip_pts = np.array([(landmarks[i].x, landmarks[i].y) for i in self.LIPS])
                lip_movement = np.std(lip_pts[:, 1]) 
                lip_sequence.append(lip_movement)
            else:
                ear_sequence.append(0)
                lip_sequence.append(0)
                
        cap.release()
        
        # Analysis: Deepfakes often lack natural facial micro-expressions
        blink_std = np.std(ear_sequence) if ear_sequence else 0
        
        # Realistic EAR standard deviation is usually > 0.01. If it's too rigid, it's suspicious.
        if blink_std < 0.005:
            inconsistency_score = 0.90 # Too stiff (often seen in basic fakes)
        elif blink_std > 0.1:
            inconsistency_score = 0.85 # Unnaturally jittery
        else:
            inconsistency_score = 0.15 # Natural range
        
        return {
            'fps': fps,
            'lip_sequence': lip_sequence,
            'blink_variance': float(blink_std), # keeping key name for compatibility
            'inconsistency_score': float(inconsistency_score)
        }
