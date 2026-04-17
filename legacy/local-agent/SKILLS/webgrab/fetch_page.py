#!/usr/bin/env python3
"""
Fetch a web page for analysis.
Usage: python fetch_page.py <url> [--output <path>] [--links|--text]
"""

import sys
import os
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)


def fetch_page(url, output_path=None, mode="html"):
    """Fetch a URL and optionally save it."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print(f"URL: {url}")
    print(f"STATUS: {response.status_code}")
    print(f"SIZE: {len(response.content)} bytes")

    content = response.text

    if mode == "links":
        # Extract links using basic regex
        import re
        links = re.findall(r'href=["\']([^"\']+)["\']', content)
        links += re.findall(r'src=["\']([^"\']+)["\']', content)
        print(f"LINKS: {len(links)} found")
        for link in links[:10]:
            print(f"  {link}")
        if len(links) > 10:
            print(f"  ... and {len(links) - 10} more")
        return links

    elif mode == "text":
        # Strip HTML tags
        import re
        text = re.sub(r'<[^>]+>', '', content)
        text = re.sub(r'\s+', ' ', text).strip()
        content = text
        print(f"TEXT_LENGTH: {len(text)} chars")

    if output_path:
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"OUTPUT: {output_path}")

    return content


def main():
    if len(sys.argv) < 2:
        print("Usage: python fetch_page.py <url> [--output <path>] [--links|--text]")
        sys.exit(1)

    url = sys.argv[1]
    output_path = None
    mode = "html"

    for i, arg in enumerate(sys.argv[2:], start=2):
        if arg == "--output" and i < len(sys.argv) - 1:
            output_path = sys.argv[i + 1]
        elif arg == "--links":
            mode = "links"
        elif arg == "--text":
            mode = "text"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(
        os.path.dirname(__file__), "..", "..", "LOGS",
        f"webgrab_{timestamp}.log"
    )
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Log the fetch
    with open(log_file, "w") as f:
        f.write(f"URL: {url}\n")
        f.write(f"MODE: {mode}\n")
        f.write(f"TIMESTAMP: {timestamp}\n")

    result = fetch_page(url, output_path, mode)

    # Append result to log
    with open(log_file, "a") as f:
        f.write(f"\nSTATUS: {200 if result else 'ERROR'}\n")
        if isinstance(result, str) and len(result) < 1000:
            f.write(f"CONTENT:\n{result}\n")

    print(f"LOG: {log_file}")


if __name__ == "__main__":
    main()