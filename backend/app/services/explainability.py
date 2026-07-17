import os
import numpy as np
import cv2
from PIL import Image

from app.services.ai_detector import AIDetectorService


class ExplainabilityService:
    GRID_SIZE = 4  # 4x4 = 16 occlusion passes. Reduce to 3 for faster/coarser results.

    @staticmethod
    def generate_heatmap(image_path: str, baseline_prob: float) -> dict:
        """
        Occlusion-based saliency (Zeiler & Fergus, 2014): the image is divided
        into a grid, each cell is occluded in turn, and the drop in the
        model's AI-probability reveals which regions most influenced the
        decision. Works for any classifier architecture, including Vision
        Transformers where classic Grad-CAM doesn't apply cleanly.
        """
        try:
            original = Image.open(image_path).convert("RGB")
            width, height = original.size

            grid = ExplainabilityService.GRID_SIZE
            cell_w = width / grid
            cell_h = height / grid

            importance = np.zeros((grid, grid), dtype=np.float32)

            avg_color = tuple(int(c) for c in np.array(original).reshape(-1, 3).mean(axis=0))

            for row in range(grid):
                for col in range(grid):
                    x1, y1 = int(col * cell_w), int(row * cell_h)
                    x2, y2 = int((col + 1) * cell_w), int((row + 1) * cell_h)

                    occluded = original.copy()
                    patch = Image.new("RGB", (x2 - x1, y2 - y1), avg_color)
                    occluded.paste(patch, (x1, y1))

                    result = AIDetectorService.detect_ai_generation_from_image(occluded)
                    importance[row, col] = max(0.0, baseline_prob - result["ai_probability"])

            if importance.max() > 0:
                importance = importance / importance.max()

            heatmap_small = (importance * 255).astype(np.uint8)
            heatmap_resized = cv2.resize(heatmap_small, (width, height), interpolation=cv2.INTER_CUBIC)
            heatmap_color = cv2.applyColorMap(heatmap_resized, cv2.COLORMAP_JET)
            heatmap_color = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)

            original_np = np.array(original)
            overlay = cv2.addWeighted(original_np, 0.6, heatmap_color, 0.4, 0)

            heatmap_filename = f"heatmap_{os.path.basename(image_path)}"
            heatmap_path = os.path.join(os.path.dirname(image_path), heatmap_filename)
            Image.fromarray(overlay).save(heatmap_path)

            max_row, max_col = np.unravel_index(np.argmax(importance), importance.shape)
            region_desc = ExplainabilityService._describe_region(max_row, max_col, grid)

            return {
                "heatmap_path": os.path.basename(heatmap_path),
                "method": "Occlusion Sensitivity Mapping",
                "most_influential_region": region_desc,
            }

        except Exception as e:
            return {"error": f"Heatmap generation failed: {str(e)}"}

    @staticmethod
    def _describe_region(row: int, col: int, grid: int) -> str:
        v_third, h_third = grid / 3, grid / 3
        vertical = "top" if row < v_third else ("bottom" if row >= 2 * v_third else "middle")
        horizontal = "left" if col < h_third else ("right" if col >= 2 * h_third else "center")
        if vertical == "middle" and horizontal == "center":
            return "center of the image"
        return f"{vertical}-{horizontal} region of the image"