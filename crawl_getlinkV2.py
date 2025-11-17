"""
crawl_getlinkV2.py

Compact utility to crawl a single page (crawl4ai) and return/save all links:
- internal (same host/registered domain)
- external (other hosts)
- media (images: png/jpg/gif/svg/webp etc. and other direct media URLs found)

Usage (PowerShell / cmd):
    python crawl_getlinkV2.py --url "https://example.com" --preview 5
    python crawl_getlinkV2.py -u "https://example.com" --save            # auto name saved in ./test
    python crawl_getlinkV2.py -u "https://example.com" --save mylinks    # saves mylinks.md in ./test
"""
from __future__ import annotations

import argparse
import asyncio
import traceback
import re
from typing import Any, Dict, List, Optional
from pathlib import Path
from urllib.parse import urlparse, urljoin, urlunparse, quote
from datetime import datetime


def _run_async(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError:
        # fallback for nested event loops (notebooks)
        try:
            import nest_asyncio

            nest_asyncio.apply()
            return asyncio.get_event_loop().run_until_complete(coro)
        except Exception:
            traceback.print_exc()
            raise


def _normalize_url_for_md(u: str, base: Optional[str] = None) -> str:
    """
    Normalize / percent-encode URL parts so links with spaces or accented chars
    become valid URIs in Markdown. If `base` provided, resolve relative URLs first.
    """
    try:
        if base:
            u = urljoin(base, u)
        p = urlparse(u)
        # percent-encode path, params, query, fragment safely
        path = quote(p.path or "", safe="/%")
        params = quote(p.params or "", safe="")
        query = quote(p.query or "", safe="=&%")
        fragment = quote(p.fragment or "", safe="")
        return urlunparse((p.scheme, p.netloc, path, params, query, fragment))
    except Exception:
        # fallback to original
        return u


async def _async_get_links(url: str, max_preview: int = 5) -> Dict[str, Any]:
    """
    Perform crawl with crawl4ai.AsyncWebCrawler and collect internal/external/media links.
    Returns dict with keys: internal, external, media
    """
    try:
        from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
    except Exception as exc:
        print("crawl4ai not installed or import failed.")
        print("Install: python -m pip install crawl4ai[playwright]")
        traceback.print_exception(type(exc), exc, exc.__traceback__)
        return {"internal": [], "external": [], "media": []}

    try:
        async with AsyncWebCrawler() as crawler:
            config = CrawlerRunConfig(
                cache_mode=CacheMode.ENABLED,
                exclude_external_links=False,
                exclude_social_media_links=False,
            )
            result = await crawler.arun(url=url, config=config)
            links = getattr(result, "links", None) or {}
            internal = links.get("internal", []) if isinstance(links, dict) else []
            external = links.get("external", []) if isinstance(links, dict) else []

            # try to find media links (images and other direct media urls) from page source/markdown
            media_items: List[Dict[str, str]] = []
            content_source = (
                getattr(result, "html", None)
                or getattr(result, "page_source", None)
                or getattr(result, "markdown", None)
                or ""
            )
            found_urls = []
            if content_source:
                # find src/href attributes ending with common media extensions
                pattern_attr = re.compile(
                    r'(?:src|href)=["\']([^"\']+\.(?:png|jpe?g|gif|webp|svg|mp4|mp3|ogg|webm))["\']',
                    flags=re.I,
                )
                found_urls += pattern_attr.findall(content_source)
                # direct http(s) urls to media
                pattern_direct = re.compile(
                    r'https?://[^\s"\'()<>]+?\.(?:png|jpe?g|gif|webp|svg|mp4|mp3|ogg|webm)',
                    flags=re.I,
                )
                found_urls += pattern_direct.findall(content_source)

            # normalize + dedupe (and percent-encode spaces etc.)
            seen = set()
            for u in found_urls:
                if not u:
                    continue
                abs_url = urljoin(url, u)
                norm = _normalize_url_for_md(abs_url, base=url)
                if norm in seen:
                    continue
                seen.add(norm)
                media_items.append({"href": norm, "text": ""})

            # CLI preview printing (normalize internal/external hrefs for display)
            print(f"Found {len(internal)} internal links")
            print(f"Found {len(external)} external links")
            print(f"Found {len(media_items)} media links")
            for link in internal[:max_preview]:
                href_raw = link.get("href") if isinstance(link, dict) else str(link)
                href = _normalize_url_for_md(href_raw, base=url)
                text = (link.get("text") if isinstance(link, dict) else "") or ""
                print(f"Internal: {href}  -- text: {text}")
            for link in external[:max_preview]:
                href_raw = link.get("href") if isinstance(link, dict) else str(link)
                href = _normalize_url_for_md(href_raw, base=url)
                text = (link.get("text") if isinstance(link, dict) else "") or ""
                print(f"External: {href}  -- text: {text}")
            for link in media_items[:max_preview]:
                print(f"Media: {link.get('href')}")

            return {"internal": internal, "external": external, "media": media_items}
    except Exception as exc:
        print("Error while getting links:")
        traceback.print_exception(type(exc), exc, exc.__traceback__)
        return {"internal": [], "external": [], "media": []}


def _safe_name_from_url(url: str) -> str:
    p = urlparse(url)
    host = (p.hostname or "links").replace(".", "_")
    path = p.path.strip("/").replace("/", "_")
    base = host + (("_" + path) if path else "")
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return f"{base or 'links'}_{ts}.md"


def save_links_markdown(links: Dict[str, List[dict]], url: str, filename: Optional[str] = None, folder: str = "./test") -> Path:
    """
    Save links dict to a markdown file under folder (default ./test).
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
    media = links.get("media", [])

    def item_to_line(it):
        if isinstance(it, dict):
            href_raw = it.get("href") or it.get("url") or ""
            href = _normalize_url_for_md(href_raw, base=url)
            text = (it.get("text") or "").strip() or href
        else:
            href = _normalize_url_for_md(str(it), base=url)
            text = href
        return f"- [{text}]({href})"

    md_lines = [
        f"# Links for {url}",
        "",
        "## Summary",
        f"- Internal links: {len(internal)}",
        f"- External links: {len(external)}",
        f"- Media links: {len(media)}",
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

    md_lines += ["", "## Media (images / audio / video)", ""]
    if media:
        md_lines += [item_to_line(it) for it in media]
    else:
        md_lines.append("_No media links found._")

    out_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Saved markdown -> {out_path}")
    return out_path


def get_links(url: str, max_preview: int = 5, save_md: Optional[str] = None) -> Dict[str, List[dict]]:
    """
    Sync wrapper. save_md:
      - None: do not save
      - "auto" or True: auto filename under ./test
      - string: use as filename (without .md optionally)
    """
    links = _run_async(_async_get_links(url, max_preview=max_preview))
    if save_md is not None:
        filename = None if save_md in ("auto", True) else str(save_md)
        save_links_markdown(links, url, filename=filename, folder="./test")
    return links


def main(argv: Optional[List[str]] = None):
    parser = argparse.ArgumentParser(description="Crawl a page and collect links (internal/external/media)")
    parser.add_argument("--url", "-u", type=str, required=True, help="URL to crawl")
    parser.add_argument("--preview", "-p", type=int, default=5, help="Number of links to preview in output")
    parser.add_argument("--save", "-s", nargs="?", const="auto", default=None,
                        help="Save links to markdown inside ./test. Optional filename (without .md). If omitted use auto name.")
    args = parser.parse_args(argv)

    save_arg = None
    if args.save is not None:
        save_arg = args.save

    get_links(args.url, max_preview=args.preview, save_md=save_arg)


if __name__ == "__main__":
    main()


# python .\crawl_getlinkV2.py -u "https://tuyensinh.ntu.edu.vn/tuyen-sinh/thong-tin-tuyen-sinh-2025" --save my_links_ntu_img_v2
# python .\crawl_getlinkV2.py -u "https://admission.tdtu.edu.vn/" --save my_links_TDTU_v3