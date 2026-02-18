"""
News-to-Insight Pipeline (AI filtered version)
"""

from __future__ import annotations

import sys
import time
import json
from typing import List, Dict, Any

import requests
import feedparser

HN_NEWEST_API = "https://hacker-news.firebaseio.com/v0/newstories.json"
HN_ITEM_API = "https://hacker-news.firebaseio.com/v0/item/{id}.json"
GOOGLE_ALERTS_FEED = "https://www.google.com/alerts/feeds/09577483079640570873/17508476745309795132"

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

def get_google_alerts_items(limit: int = 20) -> List[Dict[str, str]]:
    feed = feedparser.parse(GOOGLE_ALERTS_FEED)

    items: List[Dict[str, str]] = []
    for entry in feed.entries[:limit]:
        title = (entry.get("title") or "").strip()
        link = (entry.get("link") or "").strip()
        if not title or not link:
            continue
        items.append({"title": title, "url": link})
    return items

def main() -> int:
    limit = 30
    if len(sys.argv) >= 2:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            print("Usage: python pipeline.py [limit]")
            return 2

    ids = get_newest_story_ids(limit=limit)
    google_items = get_google_alerts_items(limit=limit)

    items: List[Dict[str, Any]] = []
    # Load previously seen story IDs
    try:
        with open("seen.json", "r") as f:
            seen_ids = set(json.load(f))
    except FileNotFoundError:
        seen_ids = set()
    try:
        with open("seen_google.json", "r") as f:
            seen_google = set(json.load(f))
    except FileNotFoundError:
        seen_google = set()

    google_items = [it for it in google_items if it["url"] not in seen_google]
    business_keywords = [
        "work", "workplace", "employee", "manager",
        "productivity", "office", "corporate",
        "enterprise", "executive", "operations",
        "hr", "finance", "sales", "marketing",
    ]

    def business_score(title: str) -> int:
        t = title.lower()
        return sum(1 for k in business_keywords if k in t)

    google_items = [it for it in google_items if business_score(it["title"]) >= 1]

    google_items = sorted(
        google_items,
        key=lambda it: business_score(it["title"]),
        reverse=True,
    )

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

    print("# Google Alerts\n")
    for it in google_items:
        print(f"- [{it['title']}]({it['url']})")

    print("\n# Hacker News\n")
    for it in items:
        print(f"- [{it['title']}]({it['url']})")

    # Persist seen items for next run (HN ids + Google URLs)
    seen_google = set()
    try:
        with open("seen_google.json", "r") as f:
            seen_google = set(json.load(f))
    except FileNotFoundError:
        seen_google = set()

    seen_ids.update(it["id"] for it in items)
    seen_google.update(it["url"] for it in google_items)

    with open("seen.json", "w") as f:
        json.dump(sorted(seen_ids), f, indent=2)

    with open("seen_google.json", "w") as f:
        json.dump(sorted(seen_google), f, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())