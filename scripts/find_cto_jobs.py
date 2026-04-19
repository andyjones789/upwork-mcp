#!/usr/bin/env python
"""Find fractional-CTO-fit jobs with the user's filter criteria."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from upwork_mcp.tools.jobs import search_jobs, JobSearchParams


QUERIES = ["fractional CTO", "technical cofounder", "technical advisor startup", "MVP technical lead"]


async def main():
    seen_ids: set[str] = set()
    all_jobs: list[dict] = []

    for q in QUERIES:
        for params in [
            JobSearchParams(
                query=q,
                experience_level="expert",
                job_type="hourly",
                hourly_rate_min=75,
                payment_verified=True,
                limit=15,
            ),
            JobSearchParams(
                query=q,
                experience_level="expert",
                job_type="fixed",
                budget_min=5000,
                payment_verified=True,
                limit=15,
            ),
        ]:
            results = await search_jobs(params)
            for job in results:
                jid = job.get("id") or job.get("url")
                if jid in seen_ids:
                    continue
                seen_ids.add(jid)
                job["_query"] = q
                all_jobs.append(job)

    print(f"\nTotal unique jobs: {len(all_jobs)}\n")

    # Post-filter: client rating >= 4.5 (0.0 treated as no-review, keep as separate bucket)
    tier_a = []  # verified + rating >= 4.5
    tier_b = []  # verified + no-rating (new client)
    for j in all_jobs:
        c = j.get("client") or {}
        if c.get("rating") and c["rating"] >= 4.5:
            tier_a.append(j)
        elif not c.get("rating"):
            tier_b.append(j)

    def fmt(j):
        c = j.get("client") or {}
        return (
            f"- {j['title']}\n"
            f"    query={j['_query']!r}  budget={j.get('budget')!r}  "
            f"duration={j.get('duration')!r}\n"
            f"    client: rating={c.get('rating')} spent={c.get('total_spent')!r} "
            f"loc={c.get('location')!r} proposals={c.get('proposals')!r}\n"
            f"    {j['url']}\n"
        )

    print("=" * 70)
    print(f"TIER A — rating ≥ 4.5 ({len(tier_a)})")
    print("=" * 70)
    for j in tier_a:
        print(fmt(j))

    print("=" * 70)
    print(f"TIER B — new/unrated client but payment verified ({len(tier_b)})")
    print("=" * 70)
    for j in tier_b:
        print(fmt(j))


if __name__ == "__main__":
    asyncio.run(main())
