"""
News-to-Insight Pipeline (AI filtered version)
"""

from __future__ import annotations

import sys
import time
import json
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
    # Load previously seen story IDs
    try:
        with open("seen.json", "r") as f:
            seen_ids = set(json.load(f))
    except FileNotFoundError:
        seen_ids = set()

    keywords = ["ai", "artificial intelligence", "llm", "agent", "model", "openai", "anthropic", "gpt"]

    for item_id in ids:
        if item_id in seen_ids:
            continue
        try:
            item = get_item(item_id)
            time.sleep(0.15)
        except Exception as e:
            print(f"[skip] {item_id}: {e}")
            continue

        title = item.get("title")
        if not title:
            continue

        url = item.get("url") or f"https://news.ycombinator.com/item?id={item_id}"

        title_lower = title.lower()
        if any(k in title_lower for k in keywords):
            items.append({"id": item_id, "title": title, "url": url})

    print("# AI threads worth a look\n")
    for it in items:
        print(f"- [{it['title']}]({it['url']})")
    # Persist seen IDs for next run
    seen_ids.update(it["id"] for it in items)
    with open("seen.json", "w") as f:
        json.dump(sorted(seen_ids), f, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())