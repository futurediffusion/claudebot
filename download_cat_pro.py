import asyncio
import random
from playwright.async_api import async_playwright
import os

async def human_flow_search(page, query):
    """
    Mutación Evolutiva: GOOGLE_ANTIBOT_TRIGGER
    Implementa el flujo humano para evitar bloqueos por navegación directa.
    """
    print("🕵️‍♂️ [Human-Flow] Fase 1: Navegando a la portada de Google...")
    await page.goto("https://www.google.com/")
    
    # Aceptar cookies si aparece el popup (modo europeo)
    try:
        accept_btn = page.locator('button:has-text("Aceptar todo"), button:has-text("Accept all")')
        if await accept_btn.count() > 0:
            await accept_btn.first.click()
    except Exception:
        pass
        
    await asyncio.sleep(random.uniform(1.0, 2.5))
    
    print(f"⌨️ [Human-Flow] Fase 2: Escribiendo '{query}' con pausas humanas...")
    # Google puede usar textarea o input para su buscador principal
    search_box = page.locator('textarea[name="q"], input[name="q"]').first
    await search_box.click()
    
    # Escribir como un humano (100-250ms entre teclas)
    await search_box.type(query, delay=random.randint(100, 250))
    await asyncio.sleep(random.uniform(0.5, 1.5))
    await search_box.press("Enter")
    
    # Esperar a que carguen los resultados web
    await page.wait_for_load_state("domcontentloaded")
    await asyncio.sleep(random.uniform(1.0, 2.0))
    
    print("🖼️ [Human-Flow] Fase 3: Clic visual en la pestaña de Imágenes...")
    # Buscar el enlace de imágenes y hacer clic físico
    images_tab = page.locator('a:has-text("Imágenes"), a:has-text("Images")').first
    await images_tab.click()
    await page.wait_for_load_state("domcontentloaded")
    await asyncio.sleep(random.uniform(1.5, 3.0))

async def download_cat():
    async with async_playwright() as p:
        # Abrir navegador con viewport realista y User-Agent
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # --- APLICAMOS LA MUTACIÓN AQUÍ ---
            await human_flow_search(page, "gatos adorables")
            
            # BUSCAR EL GATO
            print("🔍 [Búsqueda] Analizando resultados visuales...")
            await page.wait_for_selector('img')
            
            # Seleccionamos una de las primeras imágenes reales
            image_selector = 'div[data-ri="0"] img, div[data-ri="1"] img'
            await page.locator(image_selector).first.click()
            await asyncio.sleep(random.uniform(1.5, 2.5)) 
            
            # Sacar la URL de la imagen del panel lateral
            img_element = await page.wait_for_selector('img[src^="http"]:not([src*="gstatic"])')
            src = await img_element.get_attribute('src')
            
            if src:
                print(f"✅ ¡Gato encontrado! Descargando desde origen real...")
                response = await page.request.get(src)
                with open("GATO_EVOLUCIONADO.jpg", "wb") as f:
                    f.write(await response.body())
                print("🏁 Tarea completada con éxito. Gato guardado.")
            else:
                print("❌ No pude encontrar la URL de la imagen.")
                
        except Exception as e:
            print(f"❌ Fallo crítico en el flujo: {e}")
            await page.screenshot(path="debug_antibot_fail.png")
            print("📸 Captura guardada como debug_antibot_fail.png")
            
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(download_cat())
