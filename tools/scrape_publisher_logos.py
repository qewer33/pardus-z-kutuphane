#!/usr/bin/env python3
# scrape_publisher_logos.py

# Tooling script (NOT part of the shipped app). It visits each publisher's
# official website and extracts the URL of their logo image, then writes a
# {publisher name: logo URL} map to a JSON file.

# We don't ship publisher logos with the application to avoid IP infringement.

# The official site URLs below were found and verified via web search. To add a
# publisher, add a verified homepage URL to SITES and re-run.

# Requirements: requests, beautifulsoup4
#     pip install requests beautifulsoup4

# Usage:
#     python tools/scrape_publisher_logos.py [-o publisher_logos.json]

import argparse
import json
import sys
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# NOTE: We couldn't find the website of Zirve Yayınları.
# NOTE: Esen and Limit are HTTP-only.

SITES: dict[str, str] = {
    "Hız Yayınları": "https://hizyayinlari.com/",
    "İşler Yayınları": "https://isler.com.tr/",
    "Ankara Yayıncılık": "https://ankarayayincilik.com.tr/",
    "Palme Yayınevi": "https://www.palmeyayinevi.com/",
    "Esen Yayınları": "http://esenyayinlari.com/",
    "Zafer Yayınları": "https://zaferyayinlari.com.tr/",
    "Limit Yayınları": "http://limityayinlari.com.tr/",
    "Sınav Yayınları": "https://www.sinavyayin.com/",
    "Kida Yayınları": "https://www.kidayayincilik.com/",
    "Tudem Yayınları": "https://www.tudem.com/",
    "FDD Yayınları": "https://www.fonyayincilik.com.tr/",
    "Lider Yayınları": "https://lideryayin.com/",
    "Murat Yayınları": "https://muratyayinlari.com/",
    "Okyanus Yayınları": "https://okyanusyayincilik.com/",
    "Paraf Yayınları": "https://parafyayinlari.com/",
    "Puan Yayınları": "https://www.puanyayin.com/",
    "Bilgi Sarmal Yayınları": "https://bilgisarmal.com/",
    "Mileniyum Yayınları": "https://www.milenyumkitap.com/",
    "Çap Yayınları": "https://capyayinlari.com/",
    "Apotemi Yayınları": "https://www.apotemi.com.tr/",
    "345 Yayınları": "https://www.ucdortbes.com/",
    "Aydın Yayınları": "https://www.aydinyayinlari.com.tr/",
}

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
TIMEOUT = 15


def fetch(url: str) -> BeautifulSoup | None:
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  ! fetch failed: {e}", file=sys.stderr)
        return None
    return BeautifulSoup(resp.text, "html.parser")


def _abs(base: str, link: str | None) -> str | None:
    if not link:
        return None
    return urljoin(base, link.strip())


def extract_logo(base_url: str, soup: BeautifulSoup) -> str | None:
    """Best-effort logo URL, trying the most logo-like sources first."""

    # 1) an <img> that looks like a logo (class/id/alt/src mentions "logo")
    for img in soup.find_all("img"):
        haystack = " ".join(
            str(img.get(attr, "")) for attr in ("class", "id", "alt", "src")
        ).lower()
        if "logo" in haystack:
            src = img.get("src") or img.get("data-src")
            if src:
                return _abs(base_url, src)

    # 2) apple-touch-icon (usually a clean square brand icon)
    icon = soup.find("link", rel=lambda v: v and "apple-touch-icon" in v.lower())
    if icon and icon.get("href"):
        return _abs(base_url, icon["href"])

    # 3) OpenGraph image (often a banner, but better than nothing)
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        return _abs(base_url, og["content"])

    # 4) favicon as a last resort
    fav = soup.find("link", rel=lambda v: v and "icon" in v.lower())
    if fav and fav.get("href"):
        return _abs(base_url, fav["href"])

    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--output",
        default="publisher_logos.json",
        help="output JSON file (default: publisher_logos.json)",
    )
    args = parser.parse_args()

    if not SITES:
        print("SITES is empty — add verified publisher homepages first.", file=sys.stderr)
        return 1

    logos: dict[str, str | None] = {}
    for name, site in SITES.items():
        print(f"* {name} <- {site}")
        soup = fetch(site)
        logo = extract_logo(site, soup) if soup else None
        if logo:
            print(f"  logo: {logo}")
        else:
            print("  logo: NOT FOUND", file=sys.stderr)
        logos[name] = logo

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(logos, f, ensure_ascii=False, indent=2)

    found = sum(1 for v in logos.values() if v)
    print(f"\nWrote {args.output}: {found}/{len(logos)} logos found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
