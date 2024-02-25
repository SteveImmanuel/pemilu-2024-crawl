import asyncio
import os
import requests
from playwright.async_api import async_playwright, Page

TIMEOUT = 3000

async def worker(name, page: Page, queue: asyncio.Queue, BASE_URL: str):
    while True:
        link, path = await queue.get()
        print(name, 'executing')

        await page.goto(BASE_URL + link, wait_until='networkidle')
        
        if 'tps' in path.lower() or 'pos' in path.lower():
            btn = page.locator('button.btn.btn-dark.float-end', has_text='Form Pindai')
            await btn.click()
            try:
                await page.wait_for_selector('div.card-body div.row div.col-md-4', timeout=TIMEOUT)
                images = await page.query_selector_all('div.card-body div.row div.col-md-4 a img')
                print(images)
                for i, image in enumerate(images):
                    img_link = await image.get_attribute('src')
                    ext = img_link.split('.')[-1]
                    response = requests.get(img_link)
                    if response.status_code == 200:
                        os.makedirs(path, exist_ok=True)
                        with open(os.path.join(path, f'{i}.{ext}'), 'wb') as file:
                            file.write(response.content)
                    else:
                        print('Failed to download image', img_link)
            except Exception as e:
                print('Timeout on', link, path)

        else:
            items = await page.query_selector_all('table.table.table-hover tr')
            for item in items:
                data = await item.query_selector('td a')
                if data is None:
                    continue
                
                text = await data.inner_text()
                next_link = await data.get_attribute('href')
                next_path = os.path.join(path, text)
                print(next_link, next_path)
                queue.put_nowait((next_link, next_path))


        # Notify the queue that the "work item" has been processed.
        print(name, 'done')
        queue.task_done()


async def main():
    max_active_tabs = 15

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        
        pages = [await context.new_page() for _ in range(max_active_tabs)]

        queue = asyncio.LifoQueue()
        queue.put_nowait((URL, '.results'))
        # queue.put_nowait((URL, '.tps'))
        tasks = [asyncio.create_task(worker(f'worker-{i}', pages[i], queue, BASE_URL)) for i in range(max_active_tabs)]

        await queue.join()

        await asyncio.sleep(300)

        await browser.close()

BASE_URL = 'https://pemilu2024.kpu.go.id'
URL = '/pilpres/hitung-suara/'
# URL = '/pilpres/hitung-suara/11/1105/110509/1105092013/1105092013004'

asyncio.run(main())