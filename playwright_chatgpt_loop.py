import asyncio
from playwright.async_api import async_playwright
import random

async def chatgpt_conversation_loop():
    print("🔌 Conectando al 'enchufe' de Edge (Puerto 9222)...")
    
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            # Usar la pestaña activa (asumimos que ChatGPT está en la primera o activa)
            page = context.pages[0]
            
            await page.bring_to_front()
            
            print("⌨️ Buscando el cuadro de texto de ChatGPT...")
            prompt_box = page.locator('#prompt-textarea').first
            await prompt_box.wait_for(state="visible", timeout=20000)
            
            # Vamos a hacer una conversación de 2 turnos
            mensajes_a_enviar = [
                "¡Excelente! Confirmo recepción de la embajada. Para probar nuestra comunicación en bucle, cuéntame un chiste corto sobre inteligencia artificial.",
                "Jajaja, muy bueno. Como último mensaje de esta prueba de infiltración, despídete de mi creador, que nos está observando controlar su Edge en vivo."
            ]
            
            for i, mensaje in enumerate(mensajes_a_enviar, 1):
                print(f"\n" + "="*20 + f" TURNO {i} " + "="*20)
                
                # Simulamos clic en el input
                box = await prompt_box.bounding_box()
                if box:
                    await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                
                print("✍️ Escribiendo mensaje...")
                await prompt_box.fill("") # Limpiar por si acaso
                await prompt_box.type(mensaje, delay=random.randint(50, 100))
                
                await asyncio.sleep(1)
                print("📨 Enviando (presionando Enter)...")
                await prompt_box.press("Enter")
                
                print("⏳ Esperando a que termine de generar (Monitoreando el texto en vivo)...")
                await asyncio.sleep(3) # Dar tiempo a que empiece a responder
                
                assistant_messages = page.locator('div[data-message-author-role="assistant"]')
                
                # NUEVO SISTEMA INQUEBRANTABLE DE ESPERA:
                # Si el botón cambia o la UI cambia, no nos importa. 
                # Simplemente miramos el texto. Si deja de cambiar por 4 segundos, asumimos que terminó.
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
                            
                        # Imprimir un puntito para mostrar que estamos monitoreando
                        print(".", end="", flush=True)
                        
                        if stable_count >= 4: # 4 segundos de estabilidad = Respuesta finalizada
                            break
                    await asyncio.sleep(1)
                
                print("\n\n💎 RESPUESTA CAPTURADA:")
                print("-" * 50)
                print(last_text)
                print("-" * 50)
                
                print(f"⏱️ Pausa humana antes del siguiente turno...")
                await asyncio.sleep(random.uniform(3.0, 5.0))
                
            print("\n🎉 ¡VICTORIA ABSOLUTA! Bucle de conversación multiturmo completado.")
            
        except Exception as e:
            print(f"\n❌ FALLÓ EL BUCLE: {e}")

if __name__ == "__main__":
    asyncio.run(chatgpt_conversation_loop())
