# Changelog

## v1.1 — 2026-10-26
- Added evidence lineage metadata and source claim audit, blocked repeated-media pseudo-corroboration; added strict evidence gate for reports.
- Added EV/EBITDA and sum-of-the-parts models, while retaining PE, PB, and FCFF DCF; separated industrial financial-sector eligibility.
- Added bear/base/bull scenario-specific normalized net profit, EBITDA, FCFF, debt, minorities, and diluted shares; report displays methodology outputs, modeled equity value, per-share price, upside/downside and narrative operating drivers.
- Added optional non-network dry-run and OpenAI-compatible API report drafting adapter for Kimi and DeepSeek, keeping data math outside of generative models.
- Fixed report charts to display negative values rather than silently zeroing them.
- 14+ automated tests; real-market data retrieval and LLM paid API calls are not part of offline tests.
