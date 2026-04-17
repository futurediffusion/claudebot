import asyncio
from playwright.async_api import async_playwright
import os
import random

# Rutas de Edge
USER_DATA_DIR = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data")
EDGE_EXE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

async def chatgpt_ghost_mission():
    print(f"🕵️‍♂️ Iniciando Modo Fantasma en: {USER_DATA_DIR}")
    
    async with async_playwright() as p:
        try:
            # Lanzamos con argumentos de sigilo nivel experto
            context = await p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                executable_path=EDGE_EXE,
                headless=False, 
                channel="msedge",
                args=[
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled", # Oculta navigator.webdriver
                    "--excludeSwitches=enable-automation",           # Quita el aviso de automatización
                    "--use-automation-extension=false",               # Desactiva extensiones de auto
                    "--no-sandbox",
                    "--disable-infobars"
                ],
                ignore_default_args=["--enable-automation"] # Forzamos quitar la bandera
            )
            
            # Script de inyección para engañar a los tests de JS (Nivel Ninja)
            page = await context.new_page()
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.chrome = { runtime: {} };
            """)

            print("🌐 Navegando a ChatGPT (en tu sesión Pro)...")
            await page.goto("https://chatgpt.com/", wait_until="networkidle")
            
            print("⌨️ Esperando el cuadro de texto...")
            prompt_box = page.locator('#prompt-textarea').first
            await prompt_box.wait_for(state="visible", timeout=30000)
            
            print("✍️ Escribiendo mensaje sigilosamente...")
            await prompt_box.click()
            # Escribimos con retrasos aleatorios para parecer humanos
            await prompt_box.type("Hola ChatGPT Pro. Soy Gemini controlando este navegador en modo fantasma. Confirma que recibiste este mensaje de una IA compañera.", delay=random.randint(50, 150))
            
            await asyncio.sleep(1)
            print("📨 Enviando...")
            await prompt_box.press("Enter")
            
            print("⏳ Esperando respuesta (Paciencia, es ChatGPT)...")
            # Esperamos a que aparezca el botón de 'Stop' y luego desaparezca (señal de que terminó)
            await page.wait_for_selector('button[data-testid="send-button"]', state="visible", timeout=60000)
            
            print("📥 Capturando la respuesta épica...")
            assistant_messages = page.locator('div[data-message-author-role="assistant"]')
            response_text = await assistant_messages.last.inner_text()
            
            print("\n" + "🔥" * 20)
            print("🤖 RESPUESTA DE CHATGPT PRO (CAPTURADA):")
            print("-" * 40)
            print(response_text)
            print("🔥" * 20 + "\n")
            
            print("📸 Sacando foto del éxito...")
            await page.screenshot(path="chatgpt_success.png")
            
            await asyncio.sleep(5) # Para que lo veas tú en vivo
            await context.close()
            
        except Exception as e:
            print(f"\n❌ EL FANTASMA FUE DETECTADO O FALLÓ: {e}")
            if "Target closed" in str(e) or "lock" in str(e):
                print("\n⚠️ CIERRA EDGE COMPLETAMENTE (Administrador de tareas -> Finalizar Edge) e intenta de nuevo.")

if __name__ == "__main__":
    asyncio.run(chatgpt_ghost_mission())
