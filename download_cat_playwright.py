import asyncio
from playwright.async_api import async_playwright
import os

async def download_cat():
    async with async_playwright() as p:
        # 1. Abrir navegador visible para que veas la magia
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        print("Navegando a Google Imágenes...")
        await page.goto("https://www.google.com/search?q=gato&tbm=isch")
        
        # 2. Esperar a que las imágenes carguen
        await page.wait_for_selector('img')
        
        # 3. Obtener la URL de la primera imagen real
        # Buscamos imágenes que tengan una URL de origen real
        print("Buscando el mejor gato...")
        images = await page.query_selector_all('img')
        cat_url = None
        for img in images:
            src = await img.get_attribute('src')
            if src and src.startswith('http'):
                cat_url = src
                break
        
        if cat_url:
            print(f"¡Gato encontrado! Descargando desde: {cat_url[:50]}...")
            # Descargar usando la propia página para evitar bloqueos
            view_source = await page.goto(cat_url)
            content = await view_source.body()
            
            with open("GATO_PLAYWRIGHT_NATURAL.jpg", "wb") as f:
                f.write(content)
            print("✅ Gato guardado como 'GATO_PLAYWRIGHT_NATURAL.jpg'")
        else:
            print("❌ No pude encontrar una URL de imagen válida.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(download_cat())
