# Protocolo de Inferencia: Illustrious-XL en Forge WebUI

Este documento detalla la configuración técnica optimizada para generar imágenes de alta calidad con el modelo **Illustrious-XL-v2.0** utilizando el motor **Stable Diffusion Forge**.

## 1. Configuración del Servidor (Backend)
- **Modo:** API Headless (ahorro de VRAM).
- **Puerto:** `7860` (Estándar) o `7861` (Desatendido).
- **Comando de Arranque:**
  ```bash
  python launch.py --api --nowebui --skip-prepare-environment --port 7860
  ```
- **Bypass de Errores:** Si el endpoint `/sdapi/v1/sd-models` devuelve Error 500 (bug de Pydantic), validar disponibilidad mediante `/sdapi/v1/memory`.

## 2. Parámetros de Inferencia (The Golden Ratio)
Para obtener la mejor estética y evitar artefactos:
- **Pasos (Steps):** `28`
- **Sampler:** `Euler a` (Ancestral) -> Crítico para la coherencia en XL.
- **Scheduler:** `Karras` -> Asegura una convergencia suave.
- **CFG Scale:** `4` -> Evita la sobre-saturación y mantiene el estilo del modelo.
- **Resolución:** `768 x 1080` (Vertical óptimo).

## 3. Ingeniería de Prompts (Willy's Master Formula)

### Tags de Calidad (Pony/Illustrious Base)
Siempre incluir al inicio:
`score_9, score_8_up, score_7_up, masterpiece, best quality, `

### Estilo IL (Forge Preset)
Inyectar estos tags para acabado estético:
`amazing quality, very aesthetic, absurdres, newest, `

### Estructura de Prompt Positivo:
`[Score Tags] + [IL Style Tags] + [Sujeto] + [Estilo Artístico (Anime/Stylized)] + [Iluminación/Entorno]`

### Estructura de Negative Prompt:
`lowres, worst quality, bad quality, bad anatomy, score_6, score_5, score_4, [Estilos no deseados: 3d/photorealistic]`

## 4. Automatización (Python Snippet)
El script de envío debe apuntar a `http://127.0.0.1:7860/sdapi/v1/txt2img` con el payload JSON conteniendo los parámetros arriba descritos.

---
*Documentado el 2026.04.18 - Graduación de Gemini CLI en Illustrious XL.*
