import asyncio
from playwright.async_api import async_playwright

async def read_now():
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            page = next(pge for ctx in browser.contexts for pge in ctx.pages if "chatgpt.com" in pge.url)
            
            # Extraer el último mensaje del asistente SIN ESPERAR
            assistant_messages = page.locator('div[data-message-author-role="assistant"]')
            count = await assistant_messages.count()
            
            if count > 0:
                print(await assistant_messages.nth(count - 1).inner_text())
            else:
                print("No se encontraron mensajes.")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(read_now())
