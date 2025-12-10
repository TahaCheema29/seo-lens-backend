import time
import asyncio
from seo_scraper import SEOScraper
from seo_crawler import SEOCrawler, CrawlMode

    # start_url = "https://www.cachelogic.tech/"
    # start_url = "https://verdant-soft.com/"
    # start_url = "https://ahrefs.com/"
    
async def main():
    # start_url = "https://cookieandkate.com/"
    start_url = "https://verdant-soft.com/"
    start_time = time.perf_counter()

    # 1. Crawl URLs
    crawler = SEOCrawler(start_url, crawl_mode=CrawlMode.FULL_CRAWL)
    urls = await crawler.run()

    # 2. Scrape SEO Data
    scraper = SEOScraper(start_url)
    results = await scraper.run(urls)
    scraper.save_to_csv()

    print(f"⏱️ Done in {time.perf_counter() - start_time:.2f}s — {len(results)} pages analyzed")


if __name__ == "__main__":
    asyncio.run(main())