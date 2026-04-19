#!/usr/bin/env python
"""Smoke-test the rewritten search_jobs against the live CDP Chrome."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from upwork_mcp.tools.jobs import search_jobs, JobSearchParams, _build_search_url


async def main():
    cases = [
        JobSearchParams(query="fractional CTO", limit=5),
        JobSearchParams(
            query="fractional CTO",
            experience_level="expert",
            payment_verified=True,
            limit=5,
        ),
        JobSearchParams(
            query="developer",
            job_type="fixed",
            budget_min=5000,
            experience_level="expert",
            limit=3,
        ),
        JobSearchParams(
            query="developer",
            job_type="hourly",
            hourly_rate_min=75,
            experience_level="expert",
            limit=3,
        ),
    ]
    for params in cases:
        print("\n" + "=" * 70)
        print(f"QUERY: {params.model_dump(exclude_none=True)}")
        print(f"URL:   {_build_search_url(params)}")
        results = await search_jobs(params)
        print(f"FOUND: {len(results)}")
        for i, job in enumerate(results, 1):
            print(f"  [{i}] {job.get('title')!r}")
            print(f"      budget={job.get('budget')!r}  exp={job.get('experience_level')!r}")
            client = job.get("client") or {}
            print(
                f"      client: verified={client.get('payment_verified')} "
                f"rating={client.get('rating')} spent={client.get('total_spent')!r} "
                f"loc={client.get('location')!r} proposals={client.get('proposals')!r}"
            )
            print(f"      url={job.get('url')}")


if __name__ == "__main__":
    asyncio.run(main())
