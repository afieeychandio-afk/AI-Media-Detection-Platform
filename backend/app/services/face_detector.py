import cv2
import os
import numpy as np
from PIL import Image
from app.services.ai_detector import AIDetectorService

_face_cascade = None


def _get_cascade():
    global _face_cascade
    if _face_cascade is None:
        cascade_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
        _face_cascade = cv2.CascadeClassifier(cascade_path)
    return _face_cascade


class FaceDetectorService:
    """
    Detects human faces using OpenCV Haar Cascade, then runs each detected
    face crop through the AI-image classifier to produce a face-specific
    AI/deepfake likelihood score, separate from the whole-image score.
    """

    @staticmethod
    def detect_faces_in_image(image_path: str) -> dict:
        try:
            cascade = _get_cascade()
            img_bgr = cv2.imread(image_path)
            if img_bgr is None:
                return {"faces_detected": 0, "faces": [], "note": "Could not read image for face detection."}

            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            detections = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))

            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            faces = []

            for (x, y, w, h) in detections:
                margin = int(0.2 * w)
                x1 = max(0, x - margin)
                y1 = max(0, y - margin)
                x2 = min(img_rgb.shape[1], x + w + margin)
                y2 = min(img_rgb.shape[0], y + h + margin)

                face_crop = Image.fromarray(img_rgb[y1:y2, x1:x2])
                face_result = AIDetectorService.detect_ai_generation_from_image(face_crop)

                faces.append({
                    "box": {"x": int(x), "y": int(y), "width": int(w), "height": int(h)},
                    "face_ai_probability": face_result["ai_probability"],
                })

            return {
                "faces_detected": len(faces),
                "faces": faces,
            }

        except Exception as e:
            return {"faces_detected": 0, "faces": [], "note": f"Face detection failed: {str(e)}"}

    @staticmethod
    def count_faces_in_frame(frame_rgb: np.ndarray) -> int:
        """Quick face count for a single already-loaded RGB video frame."""
        try:
            cascade = _get_cascade()
            gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)
            detections = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            return len(detections)
        except Exception:
            return 0