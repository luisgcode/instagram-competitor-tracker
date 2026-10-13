# Instagram Competitor Tracker

Weekly dashboard that follows the public Instagram numbers of Dimplex and four competitors: how often they post, what gets watched, and how each account is run.

Live: https://luisgcode.github.io/instagram-competitor-tracker/

## How it is updated

1. Each week one reading per account goes into `readings/` as `YYYY-MM-DD-<handle>.md`.
2. `python build-data.py` rebuilds `data.js` from every reading. The newest numbers of a post replace the older ones, and each reading adds a point to the follower history.
3. The written analysis of each account lives in `analysis.json`.
4. Commit and push. The page updates on its own.

Only public data is used. Saves, shares, reach and Stories are private to each account and are not part of this.

Marketing Lab · Glen Dimplex Americas
