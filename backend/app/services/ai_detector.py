import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

MODEL_ID = "Organika/sdxl-detector"


class AIDetectorService:
    """
    Real AI-generated image detector using a pretrained Swin Transformer
    (Organika/sdxl-detector) fine-tuned to distinguish real photos from
    diffusion/GAN-generated images.
    """

    _processor = None
    _model = None
    _device = None

    @classmethod
    def _load(cls):
        if cls._model is None:
            print(f"[AIDetectorService] Loading model '{MODEL_ID}' (first call only)...")
            cls._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            cls._processor = AutoImageProcessor.from_pretrained(MODEL_ID)
            cls._model = AutoModelForImageClassification.from_pretrained(MODEL_ID)
            cls._model.to(cls._device)
            cls._model.eval()
            print(f"[AIDetectorService] Model loaded on {cls._device}.")

    @classmethod
    def _ai_label_index(cls) -> int:
        id2label = cls._model.config.id2label
        for idx, label in id2label.items():
            l = str(label).lower()
            if "artificial" in l or "fake" in l or "generated" in l or l == "ai":
                return int(idx)
        return 0

    @classmethod
    def detect_ai_generation_from_image(cls, image: Image.Image) -> dict:
        cls._load()
        inputs = cls._processor(images=image.convert("RGB"), return_tensors="pt")
        inputs = {k: v.to(cls._device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = cls._model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)[0]

        ai_idx = cls._ai_label_index()
        ai_probability = round(float(probs[ai_idx]), 4)
        confidence_score = round(float(probs.max()), 4)
        return {"ai_probability": ai_probability, "confidence_score": confidence_score}

    @classmethod
    def detect_ai_generation(cls, image_path: str) -> dict:
        try:
            image = Image.open(image_path)
            base = cls.detect_ai_generation_from_image(image)

            ai_probability = base["ai_probability"]
            human_probability = round(1.0 - ai_probability, 4)
            confidence_score = base["confidence_score"]

            if ai_probability > 0.8:
                detected_type = "Highly Likely AI Generated (Diffusion/GAN Artifacts)"
            elif ai_probability > 0.5:
                detected_type = "Suspicious - Possible AI Generation"
            else:
                detected_type = "Likely Authentic Camera Image"

            return {
                "ai_probability": ai_probability,
                "human_probability": human_probability,
                "confidence_score": confidence_score,
                "manipulation_score": ai_probability,
                "detected_type": detected_type,
                "model_used": MODEL_ID,
            }

        except Exception as e:
            return {
                "ai_probability": 0.0,
                "human_probability": 0.0,
                "confidence_score": 0.0,
                "manipulation_score": 0.0,
                "detected_type": f"Analysis failed: {str(e)}",
                "model_used": MODEL_ID,
            }