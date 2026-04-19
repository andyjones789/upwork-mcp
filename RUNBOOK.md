# Upwork AI-Jobs Runbook

Pick up from a cold start and re-run the AI opportunity scan.

## Repo

- Local: `/Users/andy/Documents/ClaudeCode/upwork/upwork-mcp`
- Fork: https://github.com/andyjones789/upwork-mcp (origin, main)
- Upstream: https://github.com/vanooo/upwork-mcp

## Preconditions

1. **Chrome with CDP on port 9222, logged into Upwork.**
   - Check: `curl -s http://127.0.0.1:9222/json/version` should return JSON.
   - If not running, the MCP's `client.py` will launch it via `start_chrome_with_debug()`, but a manual launch is often faster:
     ```
     "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
       --remote-debugging-port=9222 \
       --user-data-dir=$HOME/.upwork-mcp/chrome-profile \
       --no-first-run --no-default-browser-check &
     ```
   - If the browser is fresh, log into Upwork once manually — the profile dir persists cookies.

2. **Python env.** Managed by `uv`. `uv sync` once if deps are missing.

## Run the AI opportunity scan

```
cd /Users/andy/Documents/ClaudeCode/upwork/upwork-mcp
uv run python scripts/find_ai_jobs.py
```

- Sweeps 3 tiers (strategy, rag, automation) × 2 passes each (technical + buyer-vernacular).
- ~50 queries, ~5 minutes.
- Output: console summary by bucket + `scripts/ai_jobs_results.json` (raw, for re-ranking).

## Tier structure and why it matters

| Tier | Purpose | Technical queries | Buyer-vernacular queries |
|---|---|---|---|
| strategy | Fractional CTO / advisory | `AI strategy`, `fractional CTO`, `AI architecture`, `AI advisor` | `AI consultant`, `AI roadmap`, `AI audit`, `CTO for AI startup`, `technical advisor AI`, `help me add AI`, `AI integration expert`, `vibe coding expert` |
| rag | Knowledge/memory build | `RAG developer`, `retrieval augmented generation`, `LLM integration`, `vector database` | `AI brain`, `AI memory`, `chatbot my documents`, `train AI my data`, `custom GPT`, `ChatGPT for website`, `AI knowledge base`, `smart search` |
| automation | Workflow / agents | `AI automation`, `LLM pipeline`, `AI agent production`, `n8n AI` | `AI for emails`, `AI qualify leads`, `replace VA AI`, `AI phone caller`, `AI voice agent`, `AI customer support` |

**Why buyer-vernacular matters.** Non-technical founders don't search "RAG" — they say "AI brain" or "ChatGPT for my docs". Those posts attract fewer technical bidders → less price-based competition. The tradeoff: buyers often post sloppy budgets, so rely on post-filtering rather than URL filters.

## What "good" looks like (bucket definitions)

Scoring is in `scripts/find_ai_jobs.py::score()`. Summary:

- **PREMIUM (bucket 0):** payment_verified + rating ≥ 4.5 + spend ≥ $10K + Anglo/EU location.
- **STRONG (bucket 1):** verified + rating ≥ 4.5 + spend ≥ $1K, or rating ≥ 4.8, or spend ≥ $5K.
- **SPECULATIVE (bucket 2):** verified + Anglo/EU, new/unrated client.
- Below that = skip unless surprisingly specific.

Anglo/EU allowlist: US, UK, Canada, Ireland, Australia, NZ, Germany, France, Netherlands, Belgium, Luxembourg, Nordics, Switzerland, Austria, Spain, Italy, Portugal, Poland, Czech, Baltics.

## Curation rules (don't let the bucket lie)

A high-spend, high-rating client can still be posting garbage. Reject even from PREMIUM if:

- **Rate floor below senior tier** — e.g. `$5–15/hr`, `$8–12/hr`. Common for "AI marketing expert", "vibe coder", "VA-with-AI" posts. The client's spend came from unrelated work.
- **Title is actually SEO/VA/BDM/EA/designer** even if the description dabbles in AI. Not CTO-shaped.
- **50+ proposals on a 2-day-old post** = commoditized.
- **"Equity only" / "revenue share"** — skip unless you want the lottery ticket.
- **"Build me a ChatGPT clone"** or **"I need an AI website"** — unscoped fishing.

## Good-fit signals worth flagging

- Explicit "Fractional CTO" or "Technical Advisor" in title.
- Client has hired 5+ freelancers with ≥4.8 rating.
- Post describes the business problem + current stack + desired outcome (not a tech buzzword list).
- Budget posted at senior tier: hourly ≥ $75 for build / ≥ $100 for strategy, or fixed ≥ $5K for build / ≥ $10K for strategy.
- Proposals count < 20, post < 3 days old.
- Enterprise cues: "HIPAA", "SOC 2", "enterprise access", "compliance", named company (not "a client of mine").

## MCP fork — what's deployed

The MCP's `search_jobs` was hitting the wrong URL (`/nx/find-work/best-matches`, the personalized feed) and returning `[]` for every query. Fix is on `main` of the fork:

- Search URL: `/nx/search/jobs/?q=...`
- Parse `article[data-test="JobTile"]` using Upwork's stable `data-test` hooks (see `src/upwork_mcp/tools/jobs.py`).
- New filter params: `budget_min/max` → `amount=`, `hourly_rate_min` → `hourly_rate=`, `payment_verified` → `payment_verified_only=1`.
- Each job result now includes: `id`, `title`, `url`, `posted`, `budget`, `experience_level`, `duration`, `description`, `skills`, and a `client` sub-object with `payment_verified`, `rating`, `total_spent`, `location`, `proposals`.

To pull the latest on a new machine:

```
gh repo clone andyjones789/upwork-mcp
cd upwork-mcp && uv sync
```

Claude Code's MCP config at `~/.claude.json` points at the local directory — on a new machine, update that path or re-add via `claude mcp add`.

## If something breaks tomorrow

- **`search_jobs` returns `[]` again.** Upwork likely changed selectors. Re-run `scripts/recon.py` — it dumps HTML + lists every `data-test` hook on the search page. Compare to the selectors in `tools/jobs.py::_parse_job_tile` and patch.
- **Cloudflare challenge on first request.** Solve it once in the Chrome window; cookies persist.
- **Chrome won't start with CDP.** `lsof -iTCP:9222` to see if another process holds the port.
- **MCP tool calls fail but `scripts/smoke_search.py` works.** The MCP server process has an old module loaded. `pkill -f upwork-mcp` to force a restart on next tool call.

## Useful scripts

- `scripts/recon.py` — DOM recon, dumps HTML + selector counts to `scripts/recon-output/` (gitignored).
- `scripts/smoke_search.py` — tests 4 filter combinations against live session.
- `scripts/find_cto_jobs.py` — fractional-CTO-specific search (from earlier work).
- `scripts/find_ai_jobs.py` — the full 3-tier AI opportunity scan.

## Outreach: relevant MCP tools (once MCP is reconnected)

- `mcp__upwork__upwork_get_job_details(url)` — full description, connects cost, client hire history, rating breakdown.
- `mcp__upwork__upwork_get_connects_balance()` — check before spending.
- `mcp__upwork__upwork_submit_proposal(...)` — submit a proposal.
- `mcp__upwork__upwork_get_proposals(status=...)` — track pipeline.
- `mcp__upwork__upwork_send_message(...)` — follow-up after shortlisting.
