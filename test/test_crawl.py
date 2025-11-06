import asyncio
from crawl4ai import *

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            # url="https://www.nbcnews.com/business",
            # url="https://www.nbcnews.com/news/us-news/ups-plane-crash-death-toll-rises-least-9-officials-say-rcna242076",
            # url="https://admission.tdtu.edu.vn/dai-hoc/thong-bao-tuyen-sinh-dai-hoc-nam-2025-dot-bo-sung-dot-2",
            url="https://diemthi.tuyensinh247.com/diem-chuan/dai-hoc-ton-duc-thang-dtt.html",
        )
        print(result.markdown)
        # save to file
        with open("crawl_result_diemchuan.md", "w", encoding="utf-8") as f:
            f.write(result.markdown)

if __name__ == "__main__":
    asyncio.run(main())
