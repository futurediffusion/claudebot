#!/usr/bin/env python3
"""
Web Search Skill - Fetch updated info from the internet using Playwright.
Never depend only on trained knowledge.
"""

import sys
import os
import json
import requests
from pathlib import Path
from datetime import datetime

# Fix UTF-8 on Windows
sys.stdout.reconfigure(encoding='utf-8')


def fetch_with_playwright(url, selector=None, timeout=30000):
    """Fetch page content using Playwright (handles JS-rendered pages)."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(url, timeout=timeout, wait_until="networkidle")
            page.wait_for_timeout(2000)  # Wait for JS to render

            if selector:
                elements = page.query_selector_all(selector)
                content = "\n".join([e.inner_text() for e in elements])
            else:
                content = page.content()

            # Extract just body text (strip scripts/styles)
            text = page.evaluate("""
                () => {
                    const clone = document.body.cloneNode(true);
                    clone.querySelectorAll('script, style, noscript').forEach(e => e.remove());
                    return clone.innerText;
                }
            """)

            browser.close()
            return text[:5000]  # Limit to 5000 chars

        except Exception as e:
            browser.close()
            raise e


def fetch_with_requests(url):
    """Fallback: simple fetch with requests (for static pages)."""
    import requests

    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()

        # Try to extract text
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove scripts/styles
        for tag in soup(["script", "style"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        return text[:5000]

    except Exception as e:
        return f"ERROR requests: {e}"


def search_google(query, limit=5):
    """Search using Bing RSS feed."""
    import xml.etree.ElementTree as ET

    search_url = f"https://www.bing.com/search?q={requests.utils.quote(query)}&format=rss"

    try:
        resp = requests.get(search_url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })
        resp.raise_for_status()

        # Parse RSS XML
        root = ET.fromstring(resp.content)
        results = []

        for item in root.findall(".//item")[:limit]:
            title = item.find("title")
            link = item.find("link")
            if title is not None and link is not None:
                results.append({
                    "title": title.text[:200] if title.text else "",
                    "url": link.text if link.text else ""
                })

        return results

    except Exception as e:
        return [{"error": str(e)}]


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python fetch_info.py <url>                    # Fetch page content")
        print("  python fetch_info.py <url> --text            # Extract text only")
        print("  python fetch_info.py search <query>          # Search Google")
        sys.exit(1)

    url = sys.argv[1]
    mode = "html"

    if "--text" in sys.argv:
        mode = "text"

    # Search mode
    if url == "search" and len(sys.argv) > 2:
        query = " ".join(sys.argv[2:])
        print(f"Searching Bing for: {query}")
        print("-" * 50)

        results = search_google(query)
        print(f"\nTop {len(results)} results:\n")
        for i, r in enumerate(results, 1):
            if "error" in r:
                print(f"  {i}. ERROR: {r['error']}")
            else:
                print(f"  {i}. {r['title']}")
                print(f"     {r['url']}\n")
        sys.exit(0)

    # Fetch mode
    print("=" * 50)
    print("WEB FETCH")
    print("=" * 50)
    print(f"URL: {url}")
    print("-" * 50)

    # Save log
    log_dir = Path(__file__).parent.parent.parent / "LOGS"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / f"webfetch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    try:
        print("\n[1] Trying Playwright (JS-rendered pages)...")
        content = fetch_with_playwright(url)
        print("[2] Success with Playwright")
        method = "playwright"

    except Exception as e:
        print(f"[2] Playwright failed: {e}")
        print("\n[3] Falling back to requests...")
        content = fetch_with_requests(url)
        method = "requests"

    # Save to log
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"URL: {url}\n")
        f.write(f"METHOD: {method}\n")
        f.write(f"TIMESTAMP: {datetime.now().isoformat()}\n")
        f.write("-" * 50 + "\n")
        f.write(content)

    print(f"\nLOG: {log_path}")

    if mode == "text":
        print("-" * 50)
        print("CONTENT (first 2000 chars):")
        print("-" * 50)
        print(content[:2000])

    # Also save to WORKSPACE for reference
    workspace = Path(__file__).parent.parent.parent / "WORKSPACE"
    workspace.mkdir(exist_ok=True)
    out_path = workspace / f"fetched_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\nSAVED: {out_path}")


if __name__ == "__main__":
    main()