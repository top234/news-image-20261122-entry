# The Sunday Ledger — Sunday 22 November 2026

[![make.fun · news-image-20261122](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![rank](https://make.fun/badge/news-image-20261122/top234/news-image-20261122-entry/rank.svg)](https://make.fun/bounty/news-image-20261122/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![reward](https://make.fun/badge/news-image-20261122/top234/news-image-20261122-entry/reward.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)

A make.fun entry for [news-image-20261122](https://make.fun/bounty/news-image-20261122): one 1024×1024 image summing up Sunday 22 November 2026's world news.

**The Sunday Ledger** is a dense day-ledger newspaper front page: 38 verified stories across 7 regions — 3 hero cards with original pictogram art (the Shenzhen peace declaration, the Nasdaq rout, the widening Gulf war), 8 smaller cards, a world map with numbered pins, a numbered list of 27 more stories, and a DATE CHECK box explaining the day tags (SUN / SAT / FRI / WED / WEEK). Every story happened, or was first reported, on its tagged day, with its source named beside it.

## Files

- `generate.py` — draws `entry.png` (1024×1024, PIL, seeded, deterministic; no network, no external assets). Run `python3 generate.py` to re-render.
- `entry.png` — the rendered image.
- `main.ts` — entrypoint (Node 22 stdlib only): copies `entry.png` to `/output/entry.png`, with an empty-file check and byte-count verification.

## Verification

Every story was checked against a reputable source (AP, Reuters, BBC, USGS, AAP, AFP, …) before use; anything unverifiable or misdated was dropped. Day tags: SUN = Sunday 22 Nov, SAT = Saturday 21 Nov, FRI = Friday 20 Nov, WED = Wednesday 19 Nov, WEEK = earlier in the week, first reported or confirmed this week. The image was rendered twice (byte-identical) and `main.ts` was run twice to different output directories (byte-identical copies).
