import asyncio
import nest_asyncio
nest_asyncio.apply()

from crawl4ai import AsyncWebCrawler, CacheMode, BrowserConfig, CrawlerRunConfig, CacheMode

async def simple_crawl():
    crawler_run_config = CrawlerRunConfig( cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://diemthi.tuyensinh247.com/diem-chuan/dai-hoc-ton-duc-thang-dtt.html",
            config=crawler_run_config
        )
        print(result.markdown.raw_markdown[:500].replace("\n", " -- "))  # Print the first 500 characters

asyncio.run(simple_crawl())