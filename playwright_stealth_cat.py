import asyncio
from playwright.async_api import async_playwright
import random
import sys

async def stealth_cat_mission():
    async with async_playwright() as p:
        # Lanzamos el navegador visible y maximizado
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        context = await browser.new_context(
            no_viewport=True, 
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print("🕵️‍♂️ [Sigilo] Fase 1: Abriendo DuckDuckGo.com")
            await page.goto("https://duckduckgo.com")
            await asyncio.sleep(random.uniform(1.5, 2.5))
            
            print("⌨️ [Sigilo] Fase 2: Escribiendo 'gato' como un humano")
            search_box = page.locator('input[name="q"]').first
            await search_box.click()
            await search_box.type("gato", delay=random.randint(150, 300))
            await asyncio.sleep(random.uniform(0.5, 1.2))
            await search_box.press("Enter")
            
            print("🖼️ [Navegación] Fase 3: Buscando el link de Imágenes")
            # Selector infalible por texto visto en la captura
            images_link = page.get_by_role("link", name="Imágenes", exact=True)
            if await images_link.count() == 0:
                # Fallback por si acaso cambia el idioma
                images_link = page.locator('a:has-text("Imágenes"), a:has-text("Images")').first
            
            await images_link.click()
            await asyncio.sleep(random.uniform(3.0, 5.0))
            
            print("🎯 [Extracción] Fase 4: Seleccionando la primera imagen real")
            # En lugar de selectores CSS frágiles, usamos JS para encontrar la primera imagen real
            await page.evaluate("""() => {
                const imgs = Array.from(document.querySelectorAll('img'));
                const cat = imgs.find(i => i.width > 100 && i.height > 100 && !i.src.includes('logo'));
                if (cat) cat.click();
            }""")
            await asyncio.sleep(random.uniform(3.0, 5.0))
            
            print("📥 [Descarga] Fase 5: Bajando el gato")
            # Sacamos la URL de la imagen que esté en el visor (suele ser la más grande visible)
            cat_url = await page.evaluate("""() => {
                const imgs = Array.from(document.querySelectorAll('img'));
                const bigImg = imgs.find(i => i.width > 300);
                return bigImg ? bigImg.src : null;
            }""")
            
            if cat_url:
                if cat_url.startswith('//'):
                    cat_url = 'https:' + cat_url
                    
                print(f"✅ URL obtenida: {cat_url[:60]}...")
                # Usamos el contexto del navegador para la descarga para heredar cookies/agente
                response = await page.request.get(cat_url)
                with open("GATO_DUCK_STEALTH.jpg", "wb") as f:
                    f.write(await response.body())
                print("🎉 ¡MISIÓN CUMPLIDA! Gato guardado como 'GATO_DUCK_STEALTH.jpg'")
            else:
                print("❌ No pude encontrar la URL final en el visor.")
                await page.screenshot(path="debug_ddg_fail.png")
        except Exception as e:
            print(f"❌ La cagué en: {e}")
            await page.screenshot(path="debug_ddg_fail.png")
            print("📸 Captura de error guardada en 'debug_ddg_fail.png'")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(stealth_cat_mission())
