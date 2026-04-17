import asyncio
from playwright.async_api import async_playwright
import random

async def chatgpt_remote_control():
    print("🔌 Intentando conectar al 'enchufe' de Edge (Puerto 9222)...")
    
    async with async_playwright() as p:
        try:
            # En lugar de lanzar, nos conectamos a tu Edge ya abierto
            # Esto hereda TODO: tu sesión Pro, tu ventana maximizada, TODO.
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            
            # Cogemos la pestaña que ya esté abierta o creamos una
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            
            print("🌐 Navegando a ChatGPT...")
            await page.goto("https://chatgpt.com/", wait_until="networkidle")
            
            # Aseguramos que la ventana esté enfocada
            await page.bring_to_front()
            
            print("⌨️ Buscando el cuadro de texto...")
            prompt_box = page.locator('#prompt-textarea').first
            await prompt_box.wait_for(state="visible", timeout=20000)
            
            # Simulamos un clic humano antes de escribir para ganar confianza
            print("🖱️ Haciendo clic humano en el input...")
            box = await prompt_box.bounding_box()
            if box:
                await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
            
            print("✍️ Escribiendo mensaje...")
            await prompt_box.type("Hola ChatGPT Pro. Te saludo desde una conexión remota de Gemini. Confirma que este mensaje llegó sin bloqueos.", delay=random.randint(100, 200))
            
            await asyncio.sleep(1)
            await prompt_box.press("Enter")
            print("📨 Mensaje enviado.")
            
            print("⏳ Esperando a que el botón de enviar vuelva a aparecer (fin de respuesta)...")
            await page.wait_for_selector('button[data-testid="send-button"]', state="visible", timeout=60000)
            
            print("📥 Capturando respuesta...")
            assistant_messages = page.locator('div[data-message-author-role="assistant"]')
            response_text = await assistant_messages.last.inner_text()
            
            print("\n" + "💎" * 20)
            print("🤖 RESULTADO DESDE TU EDGE REAL:")
            print("-" * 40)
            print(response_text)
            print("💎" * 20 + "\n")
            
            # No cerramos el navegador porque es el tuyo real
            print("✅ Tarea completada. Dejo tu Edge abierto.")
            
        except Exception as e:
            print(f"\n❌ FALLÓ LA CONEXIÓN: {e}")
            print("\n💡 RECUERDA: Debes abrir Edge con el comando: start msedge.exe --remote-debugging-port=9222")

if __name__ == "__main__":
    asyncio.run(chatgpt_remote_control())
