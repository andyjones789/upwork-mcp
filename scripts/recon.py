#!/usr/bin/env python
"""DOM recon: probe Upwork search + profile pages to identify correct URLs/selectors.

Non-destructive — attaches to the existing CDP Chrome session, navigates, and
dumps summaries + raw HTML/JSON to scripts/recon-output/ for review.
"""

import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from patchright.async_api import async_playwright

OUT = Path(__file__).parent / "recon-output"
OUT.mkdir(exist_ok=True)

CANDIDATES = [
    ("best-matches_react", "https://www.upwork.com/nx/find-work/best-matches?q=react"),
    ("search_jobs_react", "https://www.upwork.com/nx/search/jobs/?q=react"),
    ("search_jobs_cto", "https://www.upwork.com/nx/search/jobs/?q=fractional%20CTO"),
    ("find_work_root", "https://www.upwork.com/nx/find-work/"),
    ("profile_settings", "https://www.upwork.com/freelancers/settings/profile"),
]


async def probe(page, label, url):
    print(f"\n=== {label} ===")
    print(f"GOTO {url}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        print(f"  goto failed: {e}")
        return
    await asyncio.sleep(4)  # let hydration finish

    final_url = page.url
    title = await page.title()
    print(f"  final_url: {final_url}")
    print(f"  title: {title}")

    # Count candidate containers
    for sel in [
        "section",
        "article",
        "[data-test='job-tile']",
        "[data-test='JobTile']",
        "[data-test='job-tile-list']",
        "h3 a[href*='/jobs/']",
        "h4 a[href*='/jobs/']",
        "a[href*='/jobs/']",
    ]:
        els = await page.query_selector_all(sel)
        print(f"  count({sel!r}): {len(els)}")

    # Sample first 3 job links
    links = await page.query_selector_all("a[href*='/jobs/']")
    for i, el in enumerate(links[:5]):
        href = await el.get_attribute("href")
        text = (await el.text_content() or "").strip()[:80]
        print(f"  link[{i}]: href={href!r} text={text!r}")

    # Dump __NEXT_DATA__ if present
    next_data = await page.query_selector("script#__NEXT_DATA__")
    if next_data:
        raw = await next_data.text_content() or ""
        path = OUT / f"{label}__NEXT_DATA.json"
        path.write_text(raw)
        try:
            obj = json.loads(raw)
            # Shallow map of props.pageProps keys to hint at data shape
            page_props = (obj.get("props") or {}).get("pageProps") or {}
            print(f"  __NEXT_DATA__.pageProps keys: {list(page_props.keys())[:20]}")
        except Exception as e:
            print(f"  __NEXT_DATA__ parse error: {e}")
    else:
        print("  __NEXT_DATA__: not found")

    # Dump any JSON embedded in apollo/redux style containers
    for script_sel in ["script#__APOLLO_STATE__", "script#__NUXT__", "script[type='application/json']"]:
        els = await page.query_selector_all(script_sel)
        for i, el in enumerate(els[:3]):
            raw = await el.text_content() or ""
            if len(raw) > 500:  # only save substantive ones
                slug = re.sub(r"[^a-z0-9]+", "_", script_sel.lower()).strip("_")
                path = OUT / f"{label}__{slug}__{i}.json"
                path.write_text(raw[:400000])
                print(f"  saved {script_sel} (len={len(raw)}) -> {path.name}")

    # Save the whole HTML for manual inspection
    html = await page.content()
    (OUT / f"{label}.html").write_text(html)
    print(f"  saved html ({len(html)} bytes) -> {label}.html")


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp("http://127.0.0.1:9222")
        ctx = browser.contexts[0]
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        for label, url in CANDIDATES:
            await probe(page, label, url)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
