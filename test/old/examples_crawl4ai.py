# -*- coding: utf-8 -*-
"""
examples_crawl4ai.py

Tách 9 ví dụ từ `crawl4ai_quickstart.py` thành các hàm riêng và cung cấp CLI
để chọn ví dụ chạy từ cmd.

Lưu ý:
- Các ví dụ bao gồm kiểm tra cài đặt, test browser (Playwright), crawl đơn giản,
  dynamic content, cleaning, link analysis, media handling, hooks, extraction.
- File này cố gắng xử lý trường hợp thiếu thư viện (crawl4ai / playwright) và
  in hướng dẫn nếu không thể chạy.

Cách dùng (PowerShell / cmd):
    python test\examples_crawl4ai.py --example 1
    python test\examples_crawl4ai.py  # interactive prompt

"""
from __future__ import annotations

import argparse
import asyncio
import sys
import traceback
from typing import Optional

# Helper runner for async functions. If nested event loop (like in notebooks), tries
# to use nest_asyncio if available.
def _run_async(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError as e:
        # Possibly a running loop (not common when running from cmd). Try nest_asyncio.
        try:
            import nest_asyncio

            nest_asyncio.apply()
            return asyncio.get_event_loop().run_until_complete(coro)
        except Exception:
            print("Unable to run async coroutine. Details:")
            traceback.print_exc()
            raise


# 1) Kiểm tra version / installation hints
def example_1_check_installation():
    """Print crawl4ai version if available and give instructions otherwise."""
    try:
        import crawl4ai

        # safe-version print
        ver = getattr(crawl4ai, '__version__', None)
        try:
            # Some packages provide nested objects; be defensive
            if hasattr(ver, '__version__'):
                ver = getattr(ver, '__version__')
        except Exception:
            pass
        print(f"crawl4ai version: {ver}")
    except Exception as exc:  # ImportError or other
        print("crawl4ai not available or import failed.")
        print("Install with: python -m pip install crawl4ai[playwright]")
        print("If you're on Colab, follow the original quickstart to install Playwright deps.")
        print("Import error details:")
        traceback.print_exception(type(exc), exc, exc.__traceback__)


# 2) Test Playwright browser (headless) and print page title.
def example_2_test_browser():
    """Launch Playwright chromium headless and open example.com (if Playwright installed).
    This checks the browser integration.
    """
    async def _inner():
        try:
            from playwright.async_api import async_playwright
        except Exception as exc:
            print("playwright not installed or import failed.")
            print("Install with: python -m pip install playwright")
            print("Then run: playwright install --with-deps chromium")
            traceback.print_exception(type(exc), exc, exc.__traceback__)
            return

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto('https://example.com', timeout=30_000)
                title = await page.title()
                print(f"Title: {title}")
                await browser.close()
        except Exception as exc:
            print("Error while running Playwright browser test:")
            traceback.print_exception(type(exc), exc, exc.__traceback__)

    _run_async(_inner())


# 3) Simple crawl using crawl4ai.AsyncWebCrawler
def example_3_simple_crawl():
    async def _inner():
        try:
            from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
            from crawl4ai import CacheMode
        except Exception as exc:
            print("crawl4ai not installed or import failed. See example_1 for install hints.")
            traceback.print_exception(type(exc), exc, exc.__traceback__)
            return

        url = "https://www.example.com"
        try:
            async with AsyncWebCrawler() as crawler:
                config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
                result = await crawler.arun(url=url, config=config)
                # Some results may not have markdown; be defensive
                md = getattr(result, 'markdown', None)
                raw = getattr(md, 'raw_markdown', None) if md else None
                if raw:
                    print(raw[:500].replace("\n", " -- "))
                else:
                    # Try to show raw html or text
                    html = getattr(result, 'final_html', None) or getattr(result, 'raw_html', None)
                    if html:
                        print(html[:500].replace("\n", " -- "))
                    else:
                        print("Crawl finished but no markdown/html returned. Inspect `result` object in interactive session.")
        except Exception as exc:
            print("Error while running simple crawl:")
            traceback.print_exception(type(exc), exc, exc.__traceback__)

    _run_async(_inner())


# 4) Dynamic content handling example (click JS)
def example_4_dynamic_content():
    async def _inner():
        try:
            from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
        except Exception as exc:
            print("crawl4ai not installed or import failed.")
            traceback.print_exception(type(exc), exc, exc.__traceback__)
            return

        js_code = [
            "const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More')); loadMoreButton && loadMoreButton.click();"
        ]
        try:
            async with AsyncWebCrawler() as crawler:
                config = CrawlerRunConfig(cache_mode=CacheMode.ENABLED, js_code=js_code)
                result = await crawler.arun(url="https://www.nbcnews.com/business", config=config)
                md = getattr(result, 'markdown', None)
                raw = getattr(md, 'raw_markdown', None) if md else None
                if raw:
                    print(raw[:500].replace("\n", " -- "))
                else:
                    print("No markdown returned; crawl may have failed or produced empty result.")
        except Exception as exc:
            print("Error in dynamic content example:")
            traceback.print_exception(type(exc), exc, exc.__traceback__)

    _run_async(_inner())


# 5) Content cleaning & markdown fit
def example_5_clean_content():
    async def _inner():
        try:
            from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
            from crawl4ai.content_filter_strategy import PruningContentFilter
            from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
        except Exception as exc:
            print("Required crawl4ai modules not available.")
            traceback.print_exception(type(exc), exc, exc.__traceback__)
            return

        try:
            async with AsyncWebCrawler(verbose=True) as crawler:
                config = CrawlerRunConfig(
                    cache_mode=CacheMode.ENABLED,
                    excluded_tags=['nav', 'footer', 'aside'],
                    remove_overlay_elements=True,
                    markdown_generator=DefaultMarkdownGenerator(
                        content_filter=PruningContentFilter(threshold=0.48, threshold_type="fixed", min_word_threshold=0),
                        options={"ignore_links": True}
                    ),
                )
                result = await crawler.arun(url="https://en.wikipedia.org/wiki/Apple", config=config)

                # Safely get markdown content (result.markdown may be None)
                md = getattr(result, 'markdown', None)
                raw_md = getattr(md, 'raw_markdown', '') if md else ''
                fit_md = getattr(md, 'fit_markdown', '') if md else ''

                # Compute lengths (0 when empty)
                full = len(raw_md) if raw_md else 0
                fit = len(fit_md) if fit_md else 0

                # Save full markdown
                with open("cleaned_full.md", "w", encoding="utf-8") as f_full:
                    f_full.write(raw_md or "")

                # If fit_markdown is empty, provide a sensible fallback so the user
                # still gets a "fit" version to inspect. We truncate the full
                # markdown to a reasonable size (e.g. 20k chars) as fallback.
                if not fit_md:
                    print("Note: result.markdown.fit_markdown is empty. Creating fallback trimmed markdown (first 20k chars).")
                    fallback_size = 20_000
                    fit_md_fallback = raw_md[:fallback_size]
                    with open("cleaned_fit.md", "w", encoding="utf-8") as f_fit:
                        f_fit.write(fit_md_fallback)
                    fit = len(fit_md_fallback)

                    # Helpful debugging info for why fit may be empty
                    try:
                        if md is not None:
                            md_attrs = [a for a in dir(md) if not a.startswith("_")]
                            print("markdown object attributes (sample):", md_attrs[:10])
                            # If the object exposes details about why fit was not generated,
                            # some implementations include generation metadata; show it if present.
                            meta = getattr(md, 'metadata', None) or getattr(md, 'meta', None)
                            if meta:
                                print("markdown metadata (partial):", str(meta)[:1000])
                        else:
                            print("No markdown object returned (md is None).")
                    except Exception:
                        # Don't fail on debug printing
                        pass
                else:
                    # Normal case: save fit_markdown
                    with open("cleaned_fit.md", "w", encoding="utf-8") as f_fit:
                        f_fit.write(fit_md or "")

                print(f"Full Markdown Length: {full}")
                print(f"Fit Markdown Length: {fit}")
        except Exception as exc:
            print("Error in cleaning example:")
            traceback.print_exception(type(exc), exc, exc.__traceback__)

    _run_async(_inner())


# 6) Link analysis
def example_6_link_analysis():
    async def _inner():
        try:
            from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
        except Exception as exc:
            print("crawl4ai not available.")
            traceback.print_exception(type(exc), exc, exc.__traceback__)
            return

        try:
            async with AsyncWebCrawler() as crawler:
                config = CrawlerRunConfig(cache_mode=CacheMode.ENABLED, exclude_external_links=True, exclude_social_media_links=True)
                result = await crawler.arun(url="https://www.nbcnews.com/business", config=config)
                links = getattr(result, 'links', None) or {}
                internal = links.get('internal', []) if isinstance(links, dict) else []
                external = links.get('external', []) if isinstance(links, dict) else []
                print(f"Found {len(internal)} internal links")
                print(f"Found {len(external)} external links")
                for link in internal[:5]:
                    href = link.get('href') if isinstance(link, dict) else str(link)
                    text = link.get('text') if isinstance(link, dict) else ''
                    print(f"Href: {href}\nText: {text}\n")
        except Exception as exc:
            print("Error in link analysis example:")
            traceback.print_exception(type(exc), exc, exc.__traceback__)

    _run_async(_inner())


# 7) Media handling
def example_7_media_handling():
    async def _inner():
        try:
            from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
        except Exception as exc:
            print("crawl4ai not available.")
            traceback.print_exception(type(exc), exc, exc.__traceback__)
            return

        try:
            async with AsyncWebCrawler() as crawler:
                config = CrawlerRunConfig(cache_mode=CacheMode.ENABLED, exclude_external_images=False)
                result = await crawler.arun(url="https://www.nbcnews.com/business", config=config)
                media = getattr(result, 'media', {}) or {}
                images = media.get('images', []) if isinstance(media, dict) else []
                for img in images[:5]:
                    src = img.get('src') if isinstance(img, dict) else str(img)
                    alt = img.get('alt') if isinstance(img, dict) else ''
                    score = img.get('score') if isinstance(img, dict) else ''
                    print(f"Image URL: {src}, Alt: {alt}, Score: {score}")
        except Exception as exc:
            print("Error in media handling example:")
            traceback.print_exception(type(exc), exc, exc.__traceback__)

    _run_async(_inner())


# 8) Hooks example (before_goto hook)
def example_8_hooks():
    async def before_goto(page, context, url, **kwargs):
        # Minimal example: set a custom header
        try:
            await page.set_extra_http_headers({"Custom-Header": "my-value"})
            print(f"[HOOK] before_goto - About to visit: {url}")
        except Exception:
            # page may not support set_extra_http_headers in some contexts
            pass
        return page

    async def _inner():
        try:
            from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
        except Exception as exc:
            print("crawl4ai not available.")
            traceback.print_exception(type(exc), exc, exc.__traceback__)
            return

        try:
            async with AsyncWebCrawler(config=BrowserConfig(verbose=True)) as crawler:
                # set hook
                try:
                    crawler.crawler_strategy.set_hook("before_goto", before_goto)
                except Exception as e:
                    print("Couldn't set hook on crawler.crawler_strategy; this demo will continue but hook may not be attached.")
                    traceback.print_exception(type(e), e, e.__traceback__)

                result = await crawler.arun(url="https://crawl4ai.com", config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS))
                md = getattr(result, 'markdown', None)
                raw = getattr(md, 'raw_markdown', None) if md else None
                if raw:
                    print(raw[:500].replace("\n", " -- "))
                else:
                    print("Hook demo finished; no markdown to show.")
        except Exception as exc:
            print("Error in hooks example:")
            traceback.print_exception(type(exc), exc, exc.__traceback__)

    _run_async(_inner())


# 9) Extraction strategy example (JSON/CSS extraction) - safe demonstration
def example_9_extraction_demo():
    async def _inner():
        try:
            from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
            from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
        except Exception as exc:
            print("Required crawl4ai extraction modules not available.")
            traceback.print_exception(type(exc), exc, exc.__traceback__)
            return

        schema = {
            "name": "Demo Extractor",
            "baseSelector": "section",
            "fields": [
                {"name": "title", "selector": "h1, h2", "type": "text"},
            ],
        }
        extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)
        try:
            async with AsyncWebCrawler() as crawler:
                config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, extraction_strategy=extraction_strategy)
                result = await crawler.arun(url="https://www.example.com", config=config)
                extracted = getattr(result, 'extracted_content', None)
                if extracted:
                    print(extracted[:1000])
                else:
                    print("No extracted content. Result object may contain details.")
        except Exception as exc:
            print("Error in extraction demo:")
            traceback.print_exception(type(exc), exc, exc.__traceback__)

    _run_async(_inner())


# Map of example number -> function & short description
EXAMPLES = {
    1: (example_1_check_installation, "Check crawl4ai installation / version"),
    2: (example_2_test_browser, "Test Playwright browser (open example.com)"),
    3: (example_3_simple_crawl, "Simple crawl (example.com) using crawl4ai)"),
    4: (example_4_dynamic_content, "Dynamic content example (js click)") ,
    5: (example_5_clean_content, "Content cleaning and markdown fitting example"),
    6: (example_6_link_analysis, "Link analysis demo"),
    7: (example_7_media_handling, "Media handling (images) demo"),
    8: (example_8_hooks, "Hooks example (before_goto)") ,
    9: (example_9_extraction_demo, "Extraction strategy (JsonCss) demo"),
}


def _list_examples():
    print("Available examples:")
    for i in sorted(EXAMPLES.keys()):
        print(f"  {i}: {EXAMPLES[i][1]}")


def main(argv: Optional[list[str]] = None):
    parser = argparse.ArgumentParser(description="Run Crawl4AI quickstart examples")
    parser.add_argument('--example', '-e', type=int, help='Example number to run (1-9)')
    parser.add_argument('--list', '-l', action='store_true', help='List available examples')
    args = parser.parse_args(argv)

    if args.list:
        _list_examples()
        return

    if args.example is None:
        # interactive prompt
        _list_examples()
        try:
            choice = input('Enter example number to run (or blank to exit): ').strip()
        except (KeyboardInterrupt, EOFError):
            print('\nExiting.')
            return
        if not choice:
            print('No selection. Exiting.')
            return
        try:
            idx = int(choice)
        except ValueError:
            print('Invalid number. Exiting.')
            return
    else:
        idx = args.example

    fn_entry = EXAMPLES.get(idx)
    if fn_entry is None:
        print(f'Example {idx} not found. Use --list to see options.')
        return

    fn = fn_entry[0]
    print(f"Running example {idx}: {fn_entry[1]}\n---")
    try:
        fn()
    except Exception as exc:
        print('Unhandled exception while running example:')
        traceback.print_exception(type(exc), exc, exc.__traceback__)


if __name__ == '__main__':
    main()
