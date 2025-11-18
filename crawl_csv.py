#!/usr/bin/env python3
# crawl_csv.py
"""
Generate an Excel (.xlsx) file with columns:
  id, title, link, type (internal/external), Keep (yes/no), Check (default no), time (update time check)

Usage examples:
  python crawl_csv.py --from-json links.json --out links.xlsx
  python crawl_csv.py --from-url "https://example.com" --out links.xlsx
Note: --from-url requires crawldata_getLink.get_links available (see crawldata_getLink.py).
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def normalize_link_item(it: Any) -> Dict[str, str]:
    """Return a dict with keys 'href' and 'text' from various possible item shapes."""
    if isinstance(it, dict):
        href = (it.get("href") or it.get("url") or "").strip()
        text = (it.get("text") or it.get("title") or "").strip() or href
    else:
        href = str(it).strip()
        text = href
    return {"href": href, "text": text}

def build_rows(links: Dict[str, List[Any]]) -> List[Dict[str, str]]:
    """
    Convert links dict with 'internal' and 'external' lists into rows for export.
    Defaults:
      - Keep: 'yes' for internal, 'no' for external
      - Check: 'no'
      - time: current UTC ISO timestamp
    """
    rows: List[Dict[str, str]] = []
    ts = now_iso()
    idx = 1
    for link_type in ("internal", "external"):
        items = links.get(link_type, []) or []
        for it in items:
            nl = normalize_link_item(it)
            rows.append({
                "id": str(idx),
                "title": nl["text"],
                "link": nl["href"],
                "type": link_type,
                "Keep": "yes" if link_type == "internal" else "no",
                "Check": "no",
                "time": ts,
            })
            idx += 1
    return rows

def load_links_from_json(path: Path) -> Dict[str, List[Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # Accept either a dict already shaped, or a list (assume internal)
    if isinstance(data, dict):
        return {
            "internal": data.get("internal", []) or [],
            "external": data.get("external", []) or []
        }
    elif isinstance(data, list):
        return {"internal": data, "external": []}
    else:
        raise ValueError("Unsupported JSON structure for links file")

def try_get_links_from_url(url: str, preview: int = 5) -> Dict[str, List[Any]]:
    """
    Try to import crawldata_getLink.get_links to fetch links from a URL.
    If not available, raise ImportError.
    """
    try:
        import crawldata_getLink as cl  # type: ignore
    except Exception as exc:
        raise ImportError("crawldata_getLink module not available") from exc

    if not hasattr(cl, "get_links"):
        raise ImportError("crawldata_getLink.get_links not found")
    # cl.get_links should be synchronous wrapper returning {'internal':[], 'external':[]}
    return cl.get_links(url, max_preview=preview, save_md=None)

def save_to_excel(rows: List[Dict[str, str]], out_path: Path) -> None:
    try:
        import pandas as pd
    except Exception as exc:
        raise ImportError("pandas is required to write Excel files. Install with: pip install pandas openpyxl") from exc

    df = pd.DataFrame(rows, columns=["id", "title", "link", "type", "Keep", "Check", "time"])
    # Ensure parent directory exists
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Write to Excel
    df.to_excel(out_path, index=False, engine="openpyxl")
    print(f"Wrote {len(rows)} rows -> {out_path}")

def main(argv: Optional[List[str]] = None) -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Generate Excel file of links with metadata")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--from-json", "-j", type=str, help="Path to JSON file containing {'internal': [...], 'external': [...]} or a list of links")
    group.add_argument("--from-url", "-u", type=str, help="URL to crawl (requires crawldata_getLink.get_links to be importable)")
    parser.add_argument("--preview", "-p", type=int, default=5, help="Preview limit when crawling from URL (passed to get_links)")
    parser.add_argument("--out", "-o", type=str, default=None, help="Output Excel file path (.xlsx). Default: links_<timestamp>.xlsx")
    args = parser.parse_args(argv)

    links: Dict[str, List[Any]] = {"internal": [], "external": []}
    if args.from_json:
        jpath = Path(args.from_json)
        if not jpath.exists():
            raise FileNotFoundError(f"JSON file not found: {jpath}")
        links = load_links_from_json(jpath)
    elif args.from_url:
        links = try_get_links_from_url(args.from_url, preview=args.preview)

    rows = build_rows(links)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    default_out = Path(f"links_{ts}.xlsx")
    out_path = Path(args.out) if args.out else default_out

    save_to_excel(rows, out_path)

if __name__ == "__main__":
    main()
    # how to run
    # python crawl_csv.py --from-json links.json --out links.xlsx
    # python crawl_csv.py --from-url "https://tuyensinh.ntu.edu.vn/tuyen-sinh/thong-tin-tuyen-sinh-2025" --out links.xlsx
    # python crawl_csv.py --from-url "https://admission.tdtu.edu.vn/dai-hoc/thong-bao-tuyen-sinh-dai-hoc-nam-2025-dot-bo-sung-dot-2" --out links.xlsx