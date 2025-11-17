"""
crawldata_getLink.py

Hàm tiện ích để lấy internal/external/image links từ 1 URL sử dụng crawl4ai.
Sử dụng:
    python crawldata_getLink.py --url "https://www.nbcnews.com/business" --save
Hoặc import get_links và gọi get_links(url).
"""
from __future__ import annotations

import argparse
import asyncio
import traceback
from typing import Any, Dict, List, Optional
import os
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime


def _run_async(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError:
        # Nếu có event loop đang chạy (notebook), thử nest_asyncio
        try:
            import nest_asyncio

            nest_asyncio.apply()
            return asyncio.get_event_loop().run_until_complete(coro)
        except Exception:
            traceback.print_exc()
            raise


async def _async_get_links(url: str, max_preview: int = 5) -> Dict[str, Any]:
    """
    Nội bộ: chạy crawler async và trả về dict chứa 'internal', 'external', và 'images' lists.
    """
    try:
        from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
    except Exception as exc:
        print("crawl4ai không được cài đặt hoặc import failed.")
        print("Cài đặt: python -m pip install crawl4ai[playwright]")
        traceback.print_exception(type(exc), exc, exc.__traceback__)
        return {"internal": [], "external": [], "images": []}

    try:
        async with AsyncWebCrawler() as crawler:
            config = CrawlerRunConfig(cache_mode=CacheMode.ENABLED, exclude_external_links=False, exclude_social_media_links=True)
            result = await crawler.arun(url=url, config=config)
            
            links = getattr(result, "links", None) or {}
            internal = links.get("internal", []) if isinstance(links, dict) else []
            external = links.get("external", []) if isinstance(links, dict) else []
            
            # [THAY ĐỔI] Lấy thêm danh sách images
            images = getattr(result, "images", []) or []

            # In tóm tắt nhỏ để tiện chạy từ CLI
            print(f"Found {len(internal)} internal links")
            print(f"Found {len(external)} external links")
            print(f"Found {len(images)} image links") # [THAY ĐỔI]
            
            for link in internal[:max_preview]:
                href = link.get("href") if isinstance(link, dict) else str(link)
                text = link.get("text") if isinstance(link, dict) else ""
                print(f"Internal: {href}  -- text: {text}")
            
            for link in external[:max_preview]:
                href = link.get("href") if isinstance(link, dict) else str(link)
                text = link.get("text") if isinstance(link, dict) else ""
                print(f"External: {href}  -- text: {text}")

            # [THAY ĐỔI] In preview cho images
            for img_link in images[:max_preview]:
                print(f"Image: {img_link}")

            return {"internal": internal, "external": external, "images": images} # [THAY ĐỔI]
    except Exception as exc:
        print("Lỗi khi lấy links:")
        traceback.print_exception(type(exc), exc, exc.__traceback__)
        return {"internal": [], "external": [], "images": []} # [THAY ĐỔI]


def _safe_name_from_url(url: str) -> str:
    p = urlparse(url)
    host = (p.hostname or "links").replace(".", "_")
    path = p.path.strip("/").replace("/", "_")
    base = host + (("_" + path) if path else "")
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return f"{base or 'links'}_{ts}.md"


def save_links_markdown(links: Dict[str, List[Any]], url: str, filename: Optional[str] = None, folder: str = "./test") -> Path:
    """
    Lưu links dict ra file markdown trong folder (mặc định ./test).
    Nếu filename là None -> tự sinh tên.
    Trả về Path tới file đã ghi.
    """
    folder_path = Path(folder)
    folder_path.mkdir(parents=True, exist_ok=True)

    if filename:
        fname = filename if filename.lower().endswith(".md") else f"{filename}.md"
    else:
        fname = _safe_name_from_url(url)

    out_path = folder_path / fname

    internal = links.get("internal", [])
    external = links.get("external", [])
    images = links.get("images", []) # [THAY ĐỔI]

    def item_to_line(it):
        if isinstance(it, dict):
            href = it.get("href") or it.get("url") or ""
            text = (it.get("text") or "").strip() or href
        else:
            href = str(it)
            text = href
        
        # [THAY ĐỔI] Dùng cú pháp ![text](href) cho ảnh để render
        if href.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")):
            # Lấy tên file làm text dự phòng
            alt_text = href.split("/")[-1]
            return f"- ![{alt_text}]({href})"
        return f"- [{text}]({href})"

    md_lines = [
        f"# Links for {url}",
        "",
        "## Summary",
        f"- Internal links: {len(internal)}",
        f"- External links: {len(external)}",
        f"- Image links: {len(images)}", # [THAY ĐỔI]
        "",
        "## Internal links",
        "",
    ]
    if internal:
        md_lines += [item_to_line(it) for it in internal]
    else:
        md_lines.append("_No internal links found._")

    md_lines += ["", "## External links", ""]
    if external:
        md_lines += [item_to_line(it) for it in external]
    else:
        md_lines.append("_No external links found._")

    # [THAY ĐỔI] Thêm mục Image links
    md_lines += ["", "## Image links", ""]
    if images:
        md_lines += [item_to_line(it) for it in images]
    else:
        md_lines.append("_No image links found._")


    out_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Saved markdown -> {out_path}")
    return out_path


def get_links(url: str, max_preview: int = 5, save_md: Optional[str] = None) -> Dict[str, Any]:
    """
    Đồng bộ wrapper: trả về dict {'internal': [...], 'external': [...], 'images': [...]}.
    Nếu save_md is not None:
      - If save_md == 'auto' or save_md == None -> create auto filename under ./test
      - If save_md is a string -> use it as filename (with .md appended nếu cần)
    """
    links = _run_async(_async_get_links(url, max_preview=max_preview))
    # save_md handling: caller can pass None (no save), 'auto' to auto-name, or filename
    if save_md is not None:
        filename = None if save_md == "auto" or save_md is True else str(save_md)
        save_links_markdown(links, url, filename=filename, folder="./test")
    return links


def main(argv: Optional[list[str]] = None):
    parser = argparse.ArgumentParser(description="Get links (internal/external/images) from a page using crawl4ai") # Updated desc
    parser.add_argument("--url", "-u", type=str, required=True, help="URL to crawl")
    parser.add_argument("--preview", "-p", type=int, default=5, help="Number of links to preview in output")
    parser.add_argument("--save", "-s", nargs="?", const="auto", default=None,
                        help="Save links to markdown inside ./test. Optional filename (without .md). If omitted use auto name.")
    args = parser.parse_args(argv)

    # args.save is None (don't save) or 'auto' (auto name) or a string filename
    save_arg = None
    if args.save is not None:
        save_arg = args.save  # 'auto' or provided string

    get_links(args.url, max_preview=args.preview, save_md=save_arg)


if __name__ == "__main__":
    main()