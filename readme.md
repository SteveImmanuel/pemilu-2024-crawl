# Pemilu 2024 Scraper

# Installation
```bash
pip install -r requirements.txt
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

Indonesia Pemilu 2024 Scraper

options:
  -h, --help            show this help message and exit
  --start-url START_URL
                        URL to scrape
  --output OUTPUT       Output directory
  --timeout TIMEOUT     Timeout for each request
  --workers WORKERS     Total concurrent workers
  --headless            Run in headless mode
```