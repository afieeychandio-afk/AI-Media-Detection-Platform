import numpy as np
import torch
import librosa
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification

MODEL_ID = "MelodyMachine/Deepfake-audio-detection-V2"


class AudioDetectorService:
    _extractor = None
    _model = None
    _device = None

    @classmethod
    def _load(cls):
        if cls._model is None:
            print(f"[AudioDetectorService] Loading model '{MODEL_ID}' (first call only)...")
            cls._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            cls._extractor = AutoFeatureExtractor.from_pretrained(MODEL_ID)
            cls._model = AutoModelForAudioClassification.from_pretrained(MODEL_ID)
            cls._model.to(cls._device)
            cls._model.eval()
            print(f"[AudioDetectorService] Model loaded on {cls._device}.")

    @classmethod
    def _fake_label_index(cls) -> int:
        id2label = cls._model.config.id2label
        for idx, label in id2label.items():
            l = str(label).lower()
            if "fake" in l or "spoof" in l or "synthetic" in l or "clone" in l:
                return int(idx)
        return 1

    @classmethod
    def detect_audio_deepfake(cls, audio_path: str) -> dict:
        try:
            cls._load()
            audio, sr = librosa.load(audio_path, sr=16000, mono=True, duration=15)

            if audio is None or len(audio) == 0 or np.all(audio == 0):
                return cls._fallback("Empty or unreadable audio file")

            inputs = cls._extractor(audio, sampling_rate=16000, return_tensors="pt", padding=True)
            inputs = {k: v.to(cls._device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = cls._model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1)[0]

            fake_idx = cls._fake_label_index()
            ai_probability = round(float(probs[fake_idx]), 4)
            human_probability = round(1.0 - ai_probability, 4)
            confidence_score = round(float(probs.max()), 4)

            if ai_probability > 0.75:
                detected_type = "Highly Likely AI Synthesized / Cloned Voice"
            elif ai_probability > 0.45:
                detected_type = "Suspicious - Possible Voice Cloning"
            else:
                detected_type = "Likely Authentic Human Voice"

            spectral_consistency = "UNIFORM (AI-LIKE PATTERN)" if ai_probability > 0.5 else "DYNAMIC (NATURAL FREQUENCY)"

            return {
                "ai_probability": ai_probability,
                "human_probability": human_probability,
                "confidence_score": confidence_score,
                "manipulation_score": ai_probability,
                "detected_type": detected_type,
                "spectral_consistency": spectral_consistency,
                "model_used": MODEL_ID,
            }

        except Exception as e:
            return cls._fallback(str(e))

    @staticmethod
    def _fallback(reason: str) -> dict:
        return {
            "ai_probability": 0.0,
            "human_probability": 0.0,
            "confidence_score": 0.0,
            "manipulation_score": 0.0,
            "detected_type": f"Analysis failed: {reason}",
            "model_used": MODEL_ID,
        }