import cv2
import numpy as np
from PIL import Image
from app.services.ai_detector import AIDetectorService
from app.services.face_detector import FaceDetectorService


class VideoDetectorService:
    MAX_FRAMES = 12

    @staticmethod
    def detect_video_deepfake(video_path: str) -> dict:
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return VideoDetectorService._fallback("Could not open video file")

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames <= 0:
                return VideoDetectorService._fallback("Video has no readable frames")

            sample_count = min(VideoDetectorService.MAX_FRAMES, total_frames)
            frame_indices = np.linspace(0, total_frames - 1, sample_count, dtype=int)

            ai_scores = []
            frames_with_faces = 0
            processed = 0

            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
                ret, frame = cap.read()
                if not ret:
                    continue
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                face_count = FaceDetectorService.count_faces_in_frame(rgb_frame)
                if face_count > 0:
                    frames_with_faces += 1

                pil_image = Image.fromarray(rgb_frame)
                result = AIDetectorService.detect_ai_generation_from_image(pil_image)
                ai_scores.append(result["ai_probability"])
                processed += 1

            cap.release()

            if not ai_scores:
                return VideoDetectorService._fallback("No frames could be analyzed")

            avg_ai_probability = float(np.mean(ai_scores))
            max_ai_probability = float(np.max(ai_scores))
            std_ai = float(np.std(ai_scores))

            final_score = round(max(avg_ai_probability, max_ai_probability * 0.7), 4)

            if final_score > 0.75:
                detected_type = "Highly Likely AI Generated / Deepfake Video"
            elif final_score > 0.45:
                detected_type = "Suspicious - Possible AI Manipulation"
            else:
                detected_type = "Likely Authentic Video"

            return {
                "ai_probability": final_score,
                "human_probability": round(1.0 - final_score, 4),
                "confidence_score": round(max(0.0, 1.0 - std_ai), 4),
                "manipulation_score": final_score,
                "detected_type": detected_type,
                "processed_frames": processed,
                "frames_with_faces_detected": frames_with_faces,
                "frame_scores": [round(s, 3) for s in ai_scores],
            }

        except Exception as e:
            return VideoDetectorService._fallback(str(e))

    @staticmethod
    def _fallback(reason: str) -> dict:
        return {
            "ai_probability": 0.0,
            "human_probability": 0.0,
            "confidence_score": 0.0,
            "manipulation_score": 0.0,
            "detected_type": f"Analysis failed: {reason}",
            "processed_frames": 0,
            "frames_with_faces_detected": 0,
            "frame_scores": [],
        }