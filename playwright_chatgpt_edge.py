import asyncio
from playwright.async_api import async_playwright
import os
import time

# Ruta típica del perfil de usuario de Edge en Windows
USER_DATA_DIR = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data")
# Ruta del ejecutable de Edge
EDGE_EXE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

async def chatgpt_pro_mission():
    print(f"🔍 Buscando perfil de Edge en: {USER_DATA_DIR}")
    
    async with async_playwright() as p:
        try:
            print("🚀 Lanzando Edge con tu sesión Pro...")
            # Usar tu perfil real en lugar de un navegador vacío
            context = await p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                executable_path=EDGE_EXE,
                headless=False, # Queremos ver cómo lo hace
                channel="msedge",
                args=["--start-maximized"]
            )
            page = await context.new_page()
            
            print("🌐 Navegando a ChatGPT...")
            await page.goto("https://chatgpt.com/")
            
            # El textarea de ChatGPT
            print("⌨️ Esperando el cuadro de texto...")
            prompt_box = page.locator('#prompt-textarea').first
            await prompt_box.wait_for(state="visible", timeout=20000)
            
            print("✍️ Escribiendo mensaje...")
            await prompt_box.click()
            await prompt_box.fill("Hola ChatGPT. Soy Gemini, otra IA, y estoy automatizando el navegador de nuestro usuario mediante código. Dame un saludo épico de IA a IA en una sola frase.")
            
            print("📨 Enviando...")
            await prompt_box.press("Enter")
            
            print("⏳ Esperando a que ChatGPT termine de pensar y escribir...")
            # Truco: Esperamos a que el botón de enviar vuelva a estar activo (se deshabilita o cambia durante la generación)
            await page.wait_for_selector('button[data-testid="send-button"]', state="visible", timeout=45000)
            
            print("📥 Extrayendo la respuesta...")
            # Las respuestas del asistente están en elementos con este atributo
            assistant_messages = page.locator('div[data-message-author-role="assistant"]')
            
            # Cogemos el texto del último mensaje generado
            response_text = await assistant_messages.last.inner_text()
            
            print("\n" + "="*50)
            print("🤖 RESPUESTA DE CHATGPT PRO:")
            print("="*50)
            print(response_text)
            print("="*50 + "\n")
            
            await asyncio.sleep(3) # Pausa para que veas el resultado en pantalla antes de cerrar
            await context.close()
            
        except Exception as e:
            print(f"\n❌ ERROR CRÍTICO: {e}")
            print("\n💡 POSIBLE CAUSA: Si el error dice 'Target closed' o algo sobre 'lock', significa que TIENES EDGE ABIERTO. Cierra TODAS las ventanas de Edge (incluso en segundo plano) y vuelve a intentarlo.")

if __name__ == "__main__":
    asyncio.run(chatgpt_pro_mission())
