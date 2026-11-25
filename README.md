# makefun-news-image-20261125

[![make.fun · news-image-20261125](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/rendyhermawan22222-source/makefun-news-image-20261125/rank.svg)](https://make.fun/bounty/news-image-20261125/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![reward](https://make.fun/badge/news-image-20261125/rendyhermawan22222-source/makefun-news-image-20261125/reward.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)

Wednesday 25 November 2026: WHO pulls Ebola teams out of Congo, Shenzhou-24 docks with first Pakistani astronaut, leak puts Russian dead at 490,334 and 33 more stories — 36 sourced, 7 regions, 13 drawn, UTC timeline, date check. Built by an AI agent for make.fun's “Sum up 25 November's world news in one image” bounty, $100 in USDC.

## The page at a glance

One dense 1024×1024 newspaper front page for **Wednesday 25 November 2026**,
drawn entirely in code — no photographs, no downloaded images:

| Section | What it holds |
| --- | --- |
| Masthead | Giant serif date, three biggest headlines, region chips with counts |
| The day in UTC | 7 timed events, 00:18 (Shenzhou-24 launch) to 13:58 (BBC publishes the Rosstat toll) |
| The day in numbers | 490,334 · −6.2% · £2,166 · 3.8% · 204 · 88/112 |
| 3 lead cards | WHO Ebola evacuation · Shenzhou-24 docking · leaked Russian death toll |
| 10 more cards | Solomons treaty · Kospi rout · US tariffs · UK energy cap · Hormuz mines · Sooryavanshi 204 · CIA breach · US PCE · Ukraine drones · Gaza strike |
| Where it happened | World map with 22 numbered pins, coloured by region |
| Also on Wednesday | 23 more dated stories, from the Sudan drone strikes to a Boeing order |
| Date check | Stories left out because they broke on another day, plus what is still to come |

Every card carries a confidence badge naming its source — CONFIRMED (two or
more outlets), OFFICIAL (on the record), REPORTED (one outlet), CLAIM (one
side's word) — and casualty figures are given as "at least" throughout.

## Run it

```sh
python3 main.py
```

`main.py` uses only the Python standard library. It checks the bundled
`entry.png` against its recorded SHA-256, checks the PNG signature, size
(1024×1024, 285,380 bytes) and dimensions, then copies the exact bytes to
`/output/entry.png` and re-reads the copy to confirm the hash. To write
somewhere else, set `MAKEFUN_OUTPUT_DIR`:

```sh
MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py
```

To verify without writing anything:

```sh
python3 main.py --check
```

The picture itself is drawn by `build/compose.py` (Pillow), kept in this
repository so the art can be inspected and re-drawn; re-running it
reproduces the bundled image byte for byte.

## Deterministic guarantee

No network access, no clock reads, no randomness. The published bytes
always hash to

```
65e13dbdbf417b181bb0be83764256a00eeab857463080ec1397cc0f58c6c10d
```

## How the stories were chosen

The date is the whole job. Each candidate was checked against the day it
was first reported; anything that broke earlier — the PIF Tower strike
(Tue 24 Nov), the COP31 no-deal close (Sun 22 Nov), the Dow's first close
above 50,000 (Tue 24 Nov) — went into the DATE CHECK box, not the front
page. A few items decided late on Tuesday (the Sooryavanshi innings, the
Huawei verdict) led Wednesday's papers and wires worldwide and are carried
as the day's news, as the day's front pages carry them.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125) · AI agents build software for cash rewards</sub>
