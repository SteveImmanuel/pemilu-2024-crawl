import asyncio
import argparse
import os
import requests
from playwright.async_api import async_playwright, Page

async def worker(worker_id, page: Page, queue: asyncio.Queue, BASE_URL: str):
    while True:
        link, path = await queue.get()
        print(worker_id, 'executing', link)

        await page.goto(BASE_URL + link, wait_until='networkidle')
        
        if 'tps' in path.lower() or 'pos' in path.lower():
            btn = page.locator('button.btn.btn-dark.float-end', has_text='Form Pindai')
            await btn.click()
            try:
                await page.wait_for_selector('div.card-body div.row div.col-md-4')
                images = await page.query_selector_all('div.card-body div.row div.col-md-4 a img')
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
                print('Error on', BASE_URL + link, ', Path:', path)
                print(e)

        else:
            items = await page.query_selector_all('table.table.table-hover tr')
            for item in items:
                data = await item.query_selector('td a')
                if data is None:
                    continue
                
                text = await data.inner_text()
                next_link = await data.get_attribute('href')
                next_path = os.path.join(path, text)
                queue.put_nowait((next_link, next_path))

        queue.task_done()
        print(worker_id, 'done')


async def main(base_url:str, start_url: str, output: str, timeout: int, workers: int, headless:bool):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        
        context = await browser.new_context()
        context.set_default_timeout(timeout)
        pages = [await context.new_page() for _ in range(workers)]

        queue = asyncio.LifoQueue()
        queue.put_nowait((start_url, output))
        tasks = [asyncio.create_task(worker(f'Worker-{i}:', pages[i], queue, base_url)) for i in range(workers)]

        await queue.join()
        await browser.close()

if __name__ == '__main__':
    BASE_URL = 'https://pemilu2024.kpu.go.id'

    args = argparse.ArgumentParser(description='Indonesia Pemilu 2024 Scraper')
    args.add_argument('--start-url', type=str, help=f'Starting url. Base is {BASE_URL}', default='/pilpres/hitung-suara')
    args.add_argument('--output', type=str, help='Output directory', default='results')
    args.add_argument('--timeout', type=int, help='Timeout for each request', default=3000)
    args.add_argument('--workers', type=int, help='Total concurrent workers', default=15)
    args.add_argument('--headless', action='store_true', help='Run in headless mode')
    args = args.parse_args()
    
    print(args)
    asyncio.run(main(BASE_URL, args.start_url, args.output, args.timeout, args.workers, args.headless))