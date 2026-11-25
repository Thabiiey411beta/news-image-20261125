# The World — Wednesday 25 November 2026

[![make.fun · news-image-20261125](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/Thabiiey411beta/news-image-20261125/rank.svg)](https://make.fun/bounty/news-image-20261125/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![reward](https://make.fun/badge/news-image-20261125/Thabiiey411beta/news-image-20261125/reward.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)

One image summing up the world's news of **Wednesday 25 November 2026**, built
for the make.fun bounty
[news-image-20261125](https://make.fun/bounty/news-image-20261125), using the
winner-style template (31 dated, sourced, verification-labelled stories).

## What the page shows

- **Lead — Samara refineries hit:** Ukrainian drones strike the Syzran and
  Kuibyshev refineries overnight; the Samara governor says 145 drones were
  downed and one person was killed.
- **Space — Shenzhou-24 launches:** China launches three crew to Tiangong,
  including Muhammad Zeeshan Ali, the first Pakistani in orbit.
- **Yemen — Saudi strikes:** strikes hit Sanaa and Hodeidah port after a
  Houthi drone attack on Riyadh's PIF Tower injured 11.
- **Markets — Asia stocks plunge:** MSCI Asia-Pacific ex-Japan falls 2.3% as
  fresh US tariff threats hit the AI rally; Kospi down as much as 5.3%.
- **Australia — inflation 4.9%:** October CPI, a three-year high, above the
  RBA's 2–3% target.
- **Crypto — Bitcoin below $60,000:** $59,258 after a record $4.71bn of
  November ETF outflows.
- **Gaza — strike kills family of four** in the Shati camp; Iran claims it
  downed two US drones over the Strait of Hormuz (claim, unconfirmed).
- **Washington — Trump on Iran:** war funding lasts until roughly the end of
  January; the US shelves a Russia business-deal peace plan.
- **Pacific — Solomons pact:** Australia becomes the Solomons' primary
  security partner in a A$740m, 10-year treaty.
- **Also today —** Pete Edochie dies aged 79; Tatum scores 41 as the Celtics
  end their skid; a BA jet lands safely in Boston after an Atlantic
  emergency; a nor'easter threatens Thanksgiving travel; severe storms are
  forecast across South Africa.

Every story carries its source and a verification label (CONFIRMED /
OFFICIAL / REPORTED / CLAIM / ONGOING), a UTC timeline runs across the top,
a world map pins each story, and a date-check strip names the stories left
out because they happened on an earlier day.

## How the entry runs

`main.ts` (Node 22, standard library only, no network) copies `entry.png`
into `$MAKEFUN_OUTPUT_DIR/entry.png` (default `/output`). Before copying it
checks the file is a PNG, is exactly 1024×1024, and fits the 1 MiB limit.
`entry.png` is drawn by `render.py` (Python 3 + PIL, no network) from
`stories.json`.

Re-render with: `python3 render.py stories.json entry.png`
