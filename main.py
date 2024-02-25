import asyncio
import argparse
import pickle
import os
from typing import List
from playwright.async_api import async_playwright, Page
import aiohttp

async def worker(worker_id, page: Page, queue: asyncio.Queue, ref_queue:List, BASE_URL: str):
    while True:
        with open('.queue.cache', 'wb') as file:
            pickle.dump(ref_queue, file)

        link, path = await queue.get()
        ref_queue.pop()
        print(worker_id, 'processing', BASE_URL + link)

        await page.goto(BASE_URL + link, wait_until='networkidle')
        print(worker_id, 'loaded', BASE_URL + link)
        
        if 'tps' in path.lower() or 'pos' in path.lower():
            os.makedirs(path, exist_ok=True)

            with open(os.path.join(path, 'link.txt'), 'w') as file:
                file.write(BASE_URL + link)

            btn = page.locator('button.btn.btn-dark.float-end', has_text='Form Pindai')
            await btn.click()
            try:
                await page.wait_for_selector('div.card-body div.row div.col-md-4')
                images = await page.query_selector_all('div.card-body div.row div.col-md-4 a img')
                for i, image in enumerate(images):
                    img_link = await image.get_attribute('src')
                    ext = img_link.split('.')[-1]
                    async with aiohttp.ClientSession() as session:
                        async with session.get(img_link) as response:
                            if response.status == 200:
                                with open(os.path.join(path, f'{i}.{ext}'), 'wb') as file:
                                    file.write(await response.read())
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
                ref_queue.append((next_link, next_path))

        queue.task_done()
        print(worker_id, 'done')


async def main(base_url:str, start_url: str, output: str, timeout: int, workers: int, headless:bool, resume:bool):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        
        context = await browser.new_context()
        context.set_default_timeout(timeout)
        pages = [await context.new_page() for _ in range(workers)]

        if resume and os.path.exists('.queue.cache'):
            print('Resuming previous session')
            with open('.queue.cache', 'rb') as file:
                ref_queue = pickle.load(file)
        else:
            ref_queue = [(start_url, output)]

        queue = asyncio.LifoQueue()
        for start_url, output in ref_queue:
            queue.put_nowait((start_url, output))

        tasks = [asyncio.create_task(worker(f'Worker-{i}:', pages[i], queue, ref_queue, base_url)) for i in range(workers)]
        await queue.join()
        await asyncio.gather(*tasks)
        await browser.close()

if __name__ == '__main__':
    BASE_URL = 'https://pemilu2024.kpu.go.id'

    args = argparse.ArgumentParser(description='Indonesia Pemilu 2024 Scraper')
    args.add_argument('--start-url', type=str, help=f'Starting url. Base is {BASE_URL}', default='/pilpres/hitung-suara')
    args.add_argument('--output', type=str, help='Output directory', default='results')
    args.add_argument('--timeout', type=int, help='Timeout for each request', default=3000)
    args.add_argument('--workers', type=int, help='Total concurrent workers', default=15)
    args.add_argument('--headless', action='store_true', help='Run in headless mode')
    args.add_argument('--resume', action='store_true', help='Resume previous session if available')
    args = args.parse_args()
    
    print(args)
    asyncio.run(main(BASE_URL, args.start_url, args.output, args.timeout, args.workers, args.headless, args.resume))