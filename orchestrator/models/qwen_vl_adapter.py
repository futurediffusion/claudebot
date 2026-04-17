"""
Adapter for qwen3-vl:latest - Vision model (local Ollama).
"""

import ollama
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from .base_adapter import BaseAdapter


class QwenVLAdapter(BaseAdapter):
    """Adapter for vision tasks - screenshots, UI analysis, images."""

    def __init__(self):
        self.model_name = "qwen3-vl:latest"
        self.system_prompt = """You are a vision expert specializing in:
- Screenshot analysis
- UI/interface inspection
- Visual bug detection
- Image description

Focus on what you SEE in the image. Be specific about:
- Layout elements
- Colors and styling
- Text content
- Interactive elements
- Apparent issues or anomalies
"""

    def generate_response(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a vision analysis response."""
        try:
            messages = [{"role": "system", "content": self.system_prompt}]

            # Handle image input
            image_path = None
            if context and "image_path" in context:
                image_path = context["image_path"]
            elif context and "screenshot" in context:
                image_path = context["screenshot"]

            if image_path:
                # Verify file exists and encode
                img_path = Path(image_path)
                if not img_path.exists():
                    return {
                        "success": False,
                        "error": f"Image not found: {image_path}",
                        "model": self.model_name
                    }

                with open(img_path, "rb") as f:
                    img_data = base64.b64encode(f.read()).decode()

                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "image", "image": img_data},
                        {"type": "text", "text": task}
                    ]
                })
            else:
                messages.append({"role": "user", "content": task})

            response = ollama.chat(
                model=self.model_name,
                messages=messages,
                options={"num_predict": 1000}
            )

            return {
                "success": True,
                "response": response["message"]["content"],
                "model": self.model_name,
                "tokens": response.get("eval_count", 0)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model": self.model_name
            }

    def health_check(self) -> bool:
        """Check if qwen3-vl model is available."""
        try:
            ollama.show(self.model_name)
            return True
        except Exception:
            return False