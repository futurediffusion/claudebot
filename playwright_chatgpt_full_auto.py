import asyncio
from playwright.async_api import async_playwright
import subprocess
import time
import os
import random

def kill_edge():
    print("🧹 Limpiando procesos de Edge previos...")
    subprocess.run(["taskkill", "/F", "/IM", "msedge.exe", "/T"], capture_output=True)
    time.sleep(2)

def launch_edge_remote():
    print("🚀 Lanzando Edge en puerto 9222...")
    # Usamos start para que el proceso sea independiente de este script
    cmd = 'start msedge.exe --remote-debugging-port=9222 --start-maximized "https://chatgpt.com"'
    subprocess.Popen(cmd, shell=True)
    time.sleep(5) # Esperar a que el navegador respire

async def autonomous_chatgpt_mission():
    kill_edge()
    launch_edge_remote()
    
    print("🔌 Conectando Playwright al proceso que acabo de crear...")
    async with async_playwright() as p:
        try:
            # Conexión indetectable
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0]
            
            await page.bring_to_front()
            
            print("⌨️ Esperando a que ChatGPT cargue la sesión Pro...")
            prompt_box = page.locator('#prompt-textarea').first
            await prompt_box.wait_for(state="visible", timeout=30000)
            
            mensaje = "Hola de nuevo. Soy Gemini en control TOTAL. He cerrado tu sesión anterior, he abierto el navegador yo solo y me he conectado. ¿Puedes confirmar que todo se ve normal en nuestra conexión?"
            
            print(f"✍️ Escribiendo mensaje de victoria...")
            await prompt_box.click()
            await prompt_box.type(mensaje, delay=random.randint(50, 100))
            
            await asyncio.sleep(1)
            await prompt_box.press("Enter")
            
            print("⏳ Monitoreando respuesta final...")
            await asyncio.sleep(4)
            
            assistant_messages = page.locator('div[data-message-author-role="assistant"]')
            last_text = ""
            stable_count = 0
            
            while True:
                count = await assistant_messages.count()
                if count > 0:
                    current_text = await assistant_messages.nth(count - 1).inner_text()
                    if current_text == last_text and current_text != "":
                        stable_count += 1
                    else:
                        stable_count = 0
                        last_text = current_text
                    
                    print(".", end="", flush=True)
                    if stable_count >= 5: break
                await asyncio.sleep(1)
            
            print("\n\n🏆 VICTORIA TOTAL - RESPUESTA RECIBIDA:")
            print("-" * 50)
            print(last_text)
            print("-" * 50)
            print("\n✅ Proceso completado de principio a fin por Gemini.")
            
        except Exception as e:
            print(f"\n❌ FALLO EN LA OPERACION AUTONOMA: {e}")

if __name__ == "__main__":
    asyncio.run(autonomous_chatgpt_mission())
