#!/usr/bin/env python3
"""Refresh stats.json with live TikTok + Instagram numbers.

Each source is best-effort: on any failure the previous value is kept,
so a bot-block never wipes the site's numbers.
"""
import json, re, ssl, sys, urllib.request
from datetime import date, datetime, timezone

TIKTOK = "elden.brady"
INSTAGRAM = "elden.brady"

CTX = ssl.create_default_context()
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

def fetch(url, headers=None, timeout=20):
    h = {"User-Agent": UA}
    h.update(headers or {})
    req = urllib.request.Request(url, headers=h)
    return urllib.request.urlopen(req, timeout=timeout, context=CTX).read()

def tiktok_stats():
    html = fetch(f"https://www.tiktok.com/@{TIKTOK}").decode("utf-8", "ignore")
    m = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', html, re.S)
    data = json.loads(m.group(1))
    stats = data["__DEFAULT_SCOPE__"]["webapp.user-detail"]["userInfo"]["stats"]
    return {"tiktok_followers": int(stats["followerCount"]),
            "tiktok_likes": int(stats["heartCount"])}

def instagram_stats():
    raw = fetch(
        f"https://www.instagram.com/api/v1/users/web_profile_info/?username={INSTAGRAM}",
        headers={"x-ig-app-id": "936619743392459"},
    )
    user = json.loads(raw)["data"]["user"]
    return {"instagram_followers": int(user["edge_followed_by"]["count"]),
            "instagram_posts": int(user["edge_owner_to_timeline_media"]["count"])}

def main():
    with open("stats.json") as f:
        stats = json.load(f)
    changed = False
    for name, fn in (("tiktok", tiktok_stats), ("instagram", instagram_stats)):
        try:
            fresh = fn()
            for k, v in fresh.items():
                if v and stats.get(k) != v:
                    stats[k] = v
                    changed = True
            print(f"{name}: ok {fresh}")
        except Exception as e:
            print(f"{name}: FAILED ({e}) — keeping previous values", file=sys.stderr)
    if changed:
        stats["updated"] = date.today().isoformat()
        with open("stats.json", "w") as f:
            json.dump(stats, f, indent=2)
            f.write("\n")
        print("stats.json updated")
    else:
        print("no changes")

if __name__ == "__main__":
    main()
