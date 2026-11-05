# Instagram Competitor Tracker

Weekly dashboard that follows the public Instagram numbers of Dimplex and four competitors: how often they post, what gets watched, and how each account is run.

Live: https://luisgcode.github.io/instagram-competitor-tracker/

## How it is updated

Every update follows these steps, all of them, every time:

1. One reading per account goes into `readings/` as `YYYY-MM-DD-<handle>.md`, all five with the same date and the same scope (the last 6 months).
2. `python build-data.py` rebuilds `data.js`. The newest numbers of a post replace the older ones, a post missing from a newer reading that covers its date is dropped, and each reading adds a point to the follower history. The script checks every line and prints a WARNING for anything it could not load.
3. Fix every WARNING before going on. A clean run ends with "All readings loaded clean."
4. Rewrite `analysis.json` from the new data: the headline, points, read, borrow and gaps of each account, and `_overall` (findings and plan). Every number quoted in the text comes from the current data, nothing is carried over without being checked. Set `_as_of` to the reading date. Until this is done, the script warns and the page labels the analysis as written before the last reading.
5. Commit and push. The page updates on its own.

Publish only when all five accounts carry the new reading, so every account is compared on the same dates.

Only public data is used. Saves, shares, reach and Stories are private to each account and are not part of this.

Marketing Lab · Glen Dimplex Americas
