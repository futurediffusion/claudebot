# Protocolo de Automatización Visual: Freepik Image Generator

Este protocolo establece el flujo de trabajo para que el agente maneje de forma autónoma la generación de imágenes en Freepik mediante visión artificial.

## 1. Preparación del Sistema
- **Servidor de Visión:** Debe estar activo en `http://127.0.0.1:8000/analyze`.
- **Motor:** OmniParser V2.0 (YOLOv8 + OCR Lite).
- **Entorno:** `venv_vision` con `pyautogui` y `requests`.

## 2. Flujo de Navegación (Paso a Paso)

### Fase A: Localización de Pestaña
1. Tomar captura de pantalla completa.
2. Buscar elementos con texto `image`, `gener` o `freepik`.
3. **Filtro de Seguridad:** Solo considerar elementos en la parte superior (`y < 150`) para evitar falsos positivos con el texto del chat/CLI.
4. Si no se detecta, abrir navegador y navegar a la URL de Freepik AI.

### Fase B: Inyección de Prompt
1. Realizar una segunda captura una vez activa la pestaña.
2. Localizar el área de texto con el placeholder `describe your images` o similar.
3. **Acción Sniper:**
   - Hacer clic en el centro exacto del ID detectado.
   - Ejecutar `Ctrl + A` seguido de `Backspace` para limpiar.
   - Escribir el prompt a una velocidad de `0.01s` por caracter.

### Fase C: Ejecución (Disparo)
- No buscar el botón "Generate" visualmente a menos que sea necesario.
- Usar el atajo universal: **`Ctrl + Enter`**.

## 3. Consideraciones de Diseño (Anti-Confusión)
- **Zona de Exclusión:** El script debe ignorar detecciones en la zona donde reside la ventana del agente (CLI) para evitar bucles infinitos de clics sobre sí mismo.
- **Pausas de Sincronización:** Mantener `time.sleep(1.5)` entre el cambio de pestaña y el escaneo de la UI para permitir el renderizado del navegador.

---
*Documentado el 2026.04.18 - Gemini CLI con Ojos de Dios.*
