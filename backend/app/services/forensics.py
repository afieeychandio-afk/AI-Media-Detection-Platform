import os
import json
import numpy as np
import cv2
from PIL import Image, ImageChops, ImageEnhance

try:
    from c2pa import Reader as C2paReader
    C2PA_AVAILABLE = True
except ImportError:
    C2PA_AVAILABLE = False


MIME_TYPES = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".png": "image/png", ".webp": "image/webp",
    ".mp4": "video/mp4", ".mov": "video/quicktime",
    ".webm": "video/webm", ".avi": "video/x-msvideo", ".mkv": "video/x-matroska",
    ".mp3": "audio/mpeg", ".wav": "audio/wav", ".m4a": "audio/mp4", ".flac": "audio/flac",
}


class ForensicsService:

    @staticmethod
    def analyze_metadata(image_path: str) -> dict:
        """Extracts EXIF and basic structural metadata from the image."""
        metadata = {}
        try:
            with Image.open(image_path) as img:
                metadata["format"] = img.format
                metadata["mode"] = img.mode
                metadata["size"] = f"{img.width}x{img.height}"

                info = img._getexif()
                if info:
                    exif_data = {}
                    for tag, value in info.items():
                        exif_data[str(tag)] = str(value)
                    metadata["exif"] = exif_data
                    metadata["has_exif"] = True
                else:
                    metadata["has_exif"] = False
                    metadata["exif"] = None

        except Exception as e:
            metadata["error"] = f"Failed to read metadata: {str(e)}"
        return metadata

    @staticmethod
    def run_ela(image_path: str, quality: int = 90) -> str:
        """Performs Error Level Analysis (ELA) to detect digital modification."""
        ela_filename = f"ela_{os.path.basename(image_path)}"
        ela_path = os.path.join(os.path.dirname(image_path), ela_filename)

        temp_path = image_path + ".tmp.jpg"
        try:
            original = Image.open(image_path).convert('RGB')
            original.save(temp_path, 'JPEG', quality=quality)
            compressed = Image.open(temp_path)

            ela_image = ImageChops.difference(original, compressed)

            extrema = ela_image.getextrema()
            max_diff = max([ex[1] for ex in extrema])
            if max_diff == 0:
                max_diff = 1

            scale = 255.0 / max_diff
            enhancer = ImageEnhance.Brightness(ela_image)
            ela_image = enhancer.enhance(scale)

            ela_image.save(ela_path)

            return ela_path
        except Exception as e:
            raise RuntimeError(f"ELA Analysis failed: {str(e)}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    @staticmethod
    def analyze_noise_pattern(image_path: str) -> dict:
        """
        Simplified sensor-noise analysis (PRNU-inspired). Real camera sensors
        produce noise whose local variance correlates with scene content
        (more visible noise in flat/dark areas, less in sharp textured
        areas) due to physical sensor + ISP behavior. AI-generated images
        often show unnaturally uniform noise distribution across the whole
        frame since there is no physical sensor involved.

        Note: this is a heuristic signal, not a definitive PRNU
        camera-fingerprint match (true PRNU requires a reference set of
        images known to be from the same camera).
        """
        try:
            img = cv2.imread(image_path)
            if img is None:
                return {"error": "Could not read image for noise analysis"}

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
            denoised = cv2.GaussianBlur(gray, (5, 5), 0)
            noise_residual = gray - denoised

            grid = 8
            h, w = noise_residual.shape
            cell_h, cell_w = h // grid, w // grid
            block_variances = []

            for row in range(grid):
                for col in range(grid):
                    y1, y2 = row * cell_h, (row + 1) * cell_h
                    x1, x2 = col * cell_w, (col + 1) * cell_w
                    block = noise_residual[y1:y2, x1:x2]
                    if block.size > 0:
                        block_variances.append(float(np.var(block)))

            if not block_variances:
                return {"error": "Insufficient image data for noise analysis"}

            mean_var = float(np.mean(block_variances))
            std_var = float(np.std(block_variances))
            uniformity_ratio = round(std_var / (mean_var + 1e-6), 4)

            if uniformity_ratio < 0.3:
                interpretation = "Unusually uniform noise pattern across the frame — weak indicator of AI generation or heavy denoising/smoothing."
            elif uniformity_ratio < 0.6:
                interpretation = "Moderately uniform noise pattern — inconclusive."
            else:
                interpretation = "Noise pattern varies naturally with scene content — consistent with a physical camera sensor."

            return {
                "mean_noise_variance": round(mean_var, 4),
                "noise_uniformity_ratio": uniformity_ratio,
                "interpretation": interpretation,
            }

        except Exception as e:
            return {"error": f"Noise analysis failed: {str(e)}"}

    @staticmethod
    def analyze_dct_compression(image_path: str) -> dict:
        """
        DCT coefficient analysis for JPEG double-compression artifacts.
        Re-saving/editing an image often introduces a second JPEG
        compression pass, which leaves periodic peaks in the histogram of
        quantized DCT coefficients — a classic forensic signal for
        detecting edited or re-processed images. Only meaningful for
        JPEG-family files.
        """
        ext = os.path.splitext(image_path)[1].lower()
        if ext not in (".jpg", ".jpeg"):
            return {"applicable": False, "reason": "DCT analysis only applies to JPEG images."}

        try:
            img = cv2.imread(image_path)
            if img is None:
                return {"applicable": False, "reason": "Could not read image."}

            ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
            y_channel = ycrcb[:, :, 0].astype(np.float32)

            h, w = y_channel.shape
            h_crop = h - (h % 8)
            w_crop = w - (w % 8)
            y_channel = y_channel[:h_crop, :w_crop]

            coeffs = []
            for row in range(0, h_crop, 8):
                for col in range(0, w_crop, 8):
                    block = y_channel[row:row + 8, col:col + 8]
                    dct_block = cv2.dct(block)
                    coeffs.append(dct_block[0, 1])

            coeffs = np.array(coeffs)
            rounded = np.round(coeffs).astype(int)

            if rounded.size == 0 or rounded.max() == rounded.min():
                return {"applicable": True, "double_compression_suspected": False, "note": "Insufficient DCT variation."}

            hist, _ = np.histogram(rounded, bins=range(int(rounded.min()), int(rounded.max()) + 2))

            if len(hist) < 8:
                return {"applicable": True, "double_compression_suspected": False, "note": "Insufficient DCT data."}

            fft_hist = np.abs(np.fft.rfft(hist - hist.mean()))
            if len(fft_hist) > 4:
                periodicity_score = float(np.max(fft_hist[2:]) / (np.mean(fft_hist[2:]) + 1e-6))
            else:
                periodicity_score = 0.0

            double_compression_suspected = periodicity_score > 4.0

            return {
                "applicable": True,
                "periodicity_score": round(periodicity_score, 2),
                "double_compression_suspected": double_compression_suspected,
                "interpretation": (
                    "Periodic pattern detected in DCT coefficient histogram — suggests the image "
                    "may have been JPEG-compressed more than once (possible edit/re-save)."
                    if double_compression_suspected else
                    "No strong periodicity detected in DCT coefficients — consistent with single JPEG compression."
                ),
            }

        except Exception as e:
            return {"applicable": True, "error": f"DCT analysis failed: {str(e)}"}

    @staticmethod
    def check_c2pa_metadata(file_path: str) -> dict:
        """
        Checks for C2PA Content Credentials — a cryptographically signed
        manifest that major AI platforms embed in generated media.
        """
        if not C2PA_AVAILABLE:
            return {"has_c2pa": False, "reason": "c2pa-python not installed"}

        ext = os.path.splitext(file_path)[1].lower()
        mime_type = MIME_TYPES.get(ext)
        if mime_type is None:
            return {"has_c2pa": False, "reason": f"Unsupported extension for C2PA check: {ext}"}

        manifest_store = None

        try:
            reader = C2paReader.from_file(file_path)
            manifest_store = json.loads(reader.json())
        except (AttributeError, TypeError):
            manifest_store = None
        except Exception as e:
            return {"has_c2pa": False, "reason": str(e)}

        if manifest_store is None:
            try:
                with open(file_path, "rb") as f:
                    reader = C2paReader(mime_type, f)
                    manifest_store = json.loads(reader.json())
            except Exception as e:
                return {"has_c2pa": False, "reason": str(e)}

        return ForensicsService._parse_c2pa_manifest(manifest_store)

    @staticmethod
    def _parse_c2pa_manifest(manifest_store: dict) -> dict:
        active_id = manifest_store.get("active_manifest")
        manifests = manifest_store.get("manifests", {})
        if not active_id or active_id not in manifests:
            return {"has_c2pa": False}

        manifest = manifests[active_id]
        signature_info = manifest.get("signature_info", {}) or {}
        issuer = signature_info.get("issuer", "Unknown")
        generator_names = [g.get("name", "") for g in manifest.get("claim_generator_info", [])]

        is_ai_generated = False
        software_agent = None

        for assertion in manifest.get("assertions", []):
            if str(assertion.get("label", "")).startswith("c2pa.actions"):
                for action in assertion.get("data", {}).get("actions", []):
                    source_type = (action.get("digitalSourceType") or "").lower()
                    if "trainedalgorithmicmedia" in source_type or "algorithmicmedia" in source_type or "composite" in source_type:
                        is_ai_generated = True
                        agent = action.get("softwareAgent")
                        if isinstance(agent, dict):
                            software_agent = agent.get("name")
                        elif isinstance(agent, str):
                            software_agent = agent

        return {
            "has_c2pa": True,
            "is_ai_generated": is_ai_generated,
            "issuer": issuer,
            "generator": software_agent or (generator_names[0] if generator_names else "Unknown"),
            "validation_state": manifest_store.get("validation_state", "Unknown"),
        }