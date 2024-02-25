# Pemilu 2024 Image Crawler

# Installation
```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage
Basic:
```bash
python main.py
```
Advanced:
```bash
python main.py -h
usage: main.py [-h] [--start-url START_URL] [--output OUTPUT] [--timeout TIMEOUT] [--workers WORKERS] [--headless]
               [--resume]

Indonesia Pemilu 2024 Scraper

options:
  -h, --help            show this help message and exit
  --start-url START_URL
                        Starting url. Base is https://pemilu2024.kpu.go.id
  --output OUTPUT       Output directory
  --timeout TIMEOUT     Timeout for each request
  --workers WORKERS     Total concurrent workers
  --headless            Run in headless mode
  --resume              Resume previous session if available
```