import asyncio
from playwright.async_api import async_playwright
import os

async def download_cat():
    async with async_playwright() as p:
        # Abrir navegador (con headless=False para que veas que sí lo hago)
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("Navegando a Google Imágenes de gatos...")
        await page.goto("https://www.google.com/search?q=gato&tbm=isch")
        
        # Esperar a que las imágenes carguen de verdad
        await page.wait_for_selector('img')
        
        # BUSCAR EL GATO (Usando el DOM, no píxeles)
        print("Buscando al gato en el código de la página...")
        # Seleccionamos la primera imagen que no sea un icono pequeño
        image_selector = 'div[data-ri="0"] img' # El primer resultado real de Google
        
        try:
            # Hacer clic en la imagen para abrir el panel (Opcional, pero ayuda a sacar la URL real)
            await page.click(image_selector)
            await asyncio.sleep(2) # Esperar al panel lateral
            
            # Sacar la URL de la imagen del panel lateral
            # Google usa estructuras dinámicas, pero Playwright es experto en encontrarlas
            img_element = await page.wait_for_selector('img[src^="http"]')
            src = await img_element.get_attribute('src')
            
            if src:
                print(f"✅ ¡Gato encontrado por el DOM! Descargando...")
                # Guardar el archivo
                response = await page.request.get(src)
                with open("GATO_PLAYWRIGHT_PRO.jpg", "wb") as f:
                    f.write(await response.body())
                print("🏁 Tarea completada con éxito.")
            else:
                print("❌ No pude encontrar la URL de la imagen.")
        except Exception as e:
            print(f"❌ La cagué en el proceso: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(download_cat())
