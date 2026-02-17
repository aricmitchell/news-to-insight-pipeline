"""
News-to-Insight Pipeline (starter)

Step goal:
- Fetch newest items from Hacker News
- Print a simple list of titles + links (no filtering yet)
"""

from __future__ import annotations

import sys
import time
from typing import List, Dict, Any

import requests

HN_NEWEST_API = "https://hacker-news.firebaseio.com/v0/newstories.json"
HN_ITEM_API = "https://hacker-news.firebaseio.com/v0/item/{id}.json"


def fetch_json(url: str, timeout: int = 20) -> Any:
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()


def get_newest_story_ids(limit: int = 30) -> List[int]:
    ids = fetch_json(HN_NEWEST_API)
    if not isinstance(ids, list):
        raise TypeError("Unexpected response format for newest stories.")
    return [int(x) for x in ids[:limit]]


def get_item(item_id: int) -> Dict[str, Any]:
    url = HN_ITEM_API.format(id=item_id)
    data = fetch_json(url)
    if not isinstance(data, dict):
        raise TypeError(f"Unexpected item format for id={item_id}")
    return data


def main() -> int:
    limit = 30
    if len(sys.argv) >= 2:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            print("Usage: python pipeline.py [limit]")
            return 2

    ids = get_newest_story_ids(limit=limit)

    items: List[Dict[str, Any]] = []
    for i, item_id in enumerate(ids, start=1):
        try:
            item = get_item(item_id)
            # Be polite to the API
            time.sleep(0.15)
        except Exception as e:
            print(f"[skip] {item_id}: {e}")
            continue

        # Only keep stories with a title
        title = item.get("title")
        if not title:
            continue

        url = item.get("url") or f"https://news.ycombinator.com/item?id={item_id}"
        items.append({"id": item_id, "title": title, "url": url})

    for idx, it in enumerate(items, start=1):
        print(f"{idx:02d}. {it['title']}\n    {it['url']}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
