import asyncio
from crawl4ai import *

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            # url="https://admission.tdtu.edu.vn/dai-hoc/thong-bao-tuyen-sinh-dai-hoc-nam-2025-dot-bo-sung-dot-2",
            url="https://www.tdtu.edu.vn/",
            # url="https://diemthi.tuyensinh247.com/diem-chuan/dai-hoc-ton-duc-thang-dtt.html",
        )
        print(result.markdown)
        # save to file
        # E:\DoCode\CrawlData_Uni\test\TestTDTU
        with open(".\\test\\TestTDTU\\crawl_result_tdtueduvn.md", "w", encoding="utf-8") as f:
            f.write(result.markdown)

if __name__ == "__main__":
    asyncio.run(main())
