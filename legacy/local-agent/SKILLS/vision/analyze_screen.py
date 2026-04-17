#!/usr/bin/env python3
"""
Vision Analysis - Uses Ollama with vision-capable model to analyze images.
Takes a screenshot and asks the model to describe it.
"""

import sys
import os
import base64
import json
from pathlib import Path
from datetime import datetime

# Try to import Pillow for screenshot
try:
    from PIL import ImageGrab, Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def take_screenshot():
    """Take screenshot and save to WORKSPACE."""
    if not PIL_AVAILABLE:
        print("ERROR: Pillow not available for screenshots")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    workspace = Path(__file__).parent.parent.parent / "WORKSPACE"
    workspace.mkdir(exist_ok=True)

    screenshot_path = workspace / f"screenshot_{timestamp}.png"

    try:
        img = ImageGrab.grab()
        img.save(screenshot_path)
        print(f"SCREENSHOT: {screenshot_path}")
        return str(screenshot_path)
    except Exception as e:
        print(f"ERROR: {e}")
        return None


def encode_image(image_path):
    """Encode image to base64."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def analyze_with_ollama(image_path, prompt="Describe qué hay en esta imagen en español. Sé específico."):
    """Send image to Ollama for vision analysis."""
    image_b64 = encode_image(image_path)

    payload = {
        "model": "llava-llama3:latest",
        "prompt": prompt,
        "images": [image_b64],
        "stream": False
    }

    # Call Ollama API
    try:
        import urllib.request
        import urllib.error

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result.get("response", "Sin respuesta")

    except Exception as e:
        return f"ERROR Ollama: {e}"


def main():
    # Fix UTF-8 on Windows
    sys.stdout.reconfigure(encoding='utf-8')

    # 1. Take screenshot
    print("=" * 50)
    print("VISION ANALYSIS")
    print("=" * 50)
    print("\n[1] Tomando screenshot...")

    screenshot_path = take_screenshot()
    if not screenshot_path:
        print("Fallo al tomar screenshot")
        sys.exit(1)

    # 2. Analyze with Ollama
    print("\n[2] Analizando con llava via Ollama...")
    print("    Prompt: ¿Qué hay en esta imagen?\n")

    analysis = analyze_with_ollama(
        screenshot_path,
        """Eres un asistente de vision para un programador. Analiza esta pantalla y dame UN INFORME ESTRUCTURADO:

1. TEXTO EXACTO: Transcribe TODO el texto visible, palabra por palabra. Errores, comandos, nombres de archivos. Todo.
2. APLICACIONES: Qué apps/janelas hay abiertas exactamente
3. ERRORES: Si hay errores, copy-pastea el mensaje exacto del error
4. CONTEXTO: En qué está trabajando el usuario (coding, browser, terminal?)
5. LO QUE IMPORTA: Qué cosas son actionables para un programador que está trabajando

Sé preciso y detallado. No seas vago."""
    )

    print("-" * 50)
    print("ANÁLISIS:")
    print("-" * 50)
    print(analysis)
    print("-" * 50)

    # 3. Save analysis to log
    log_dir = Path(__file__).parent.parent.parent / "LOGS"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / f"vision_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"SCREENSHOT: {screenshot_path}\n")
        f.write(f"TIMESTAMP: {datetime.now().isoformat()}\n")
        f.write("-" * 50 + "\n")
        f.write("ANÁLISIS:\n")
        f.write(analysis)

    print(f"\nLOG: {log_path}")


if __name__ == "__main__":
    main()