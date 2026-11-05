"""Builds data.js for the dashboard from the reading files in readings/.

Each reading is one markdown file named YYYY-MM-DD-<handle>.md with:
  - a PART A line holding: <n> followers | <n> following | <n> posts
  - a fenced block with one pipe separated line per post (17 columns)
The newest reading of a post wins, so numbers refresh week after week, and every
reading adds one point to the follower history.

Run:  python build-data.py
"""
import io, os, re, json, glob

HERE = os.path.dirname(os.path.abspath(__file__))
SCOPE_START = "2026-07-13"

ACCOUNTS = [
    {"handle": "dimplex_northamerica", "name": "Dimplex", "us": True, "color": "--s1"},
    {"handle": "davincifire", "name": "DaVinci", "us": False, "color": "--s2"},
    {"handle": "modernflamesusa", "name": "Modern Flames", "us": False, "color": "--s3"},
    {"handle": "valorfireplaces", "name": "Valor", "us": False, "color": "--s4"},
    {"handle": "napoleonfireplace", "name": "Napoleon", "us": False, "color": "--s5"},
]
COLS = ["url", "date", "weekday", "hour", "format", "likes", "comments", "views", "slides",
        "seconds", "hashtags", "collab", "visual", "topic", "text_on_media", "cta", "caption"]


def num(v):
    v = v.strip().replace(",", "")
    try:
        return float(v) if "." in v else int(v)
    except ValueError:
        return None


FORMATS = {"Reel", "Carousel", "Photo"}
WARN = []


def code_of(url):
    m = re.search(r"/(?:p|reel|tv)/([A-Za-z0-9_-]+)", url)
    return m.group(1) if m else url


def check(path, i, r):
    """Flags a post line that would load wrong, so nothing on the page rests on a bad value."""
    where = "%s line %d" % (os.path.basename(path), i)
    if not re.match(r"\d{4}-\d{2}-\d{2}$", r["date"]):
        WARN.append("%s: bad date %r" % (where, r["date"]))
    if not re.match(r"\d{1,2}:\d{2}$", r["hour"]):
        WARN.append("%s: bad hour %r" % (where, r["hour"]))
    if r["format"] not in FORMATS:
        WARN.append("%s: unknown format %r" % (where, r["format"]))
    for k in ("comments", "views", "likes"):
        v = r[k].strip().lower()
        if v not in ("n/a", "hidden", "") and num(r[k]) is None:
            WARN.append("%s: %s is not a number %r" % (where, k, r[k]))
    if r["format"] == "Reel" and num(r["views"]) is None:
        WARN.append("%s: Reel without a view count" % where)
    if num(r["comments"]) is None:
        WARN.append("%s: comments missing" % where)


def parse(path):
    txt = io.open(path, encoding="utf-8").read()
    m = re.search(r"([\d,]+)\s+followers\s*\|\s*([\d,]+)\s+following\s*\|\s*([\d,]+)\s+posts", txt)
    profile = {"followers": num(m.group(1)), "following": num(m.group(2)), "posts_total": num(m.group(3))} if m else {}
    sc = re.search(r"Scope: posts from (\d{4}-\d{2}-\d{2})", txt)
    if sc:
        profile["scope_from"] = sc.group(1)
    posts = []
    block = re.search(r"```\n(.*?)```", txt, re.S)
    for i, line in enumerate(block.group(1).splitlines() if block else [], 1):
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split(" | ")]
        if len(parts) < len(COLS) or not parts[0].startswith("http"):
            WARN.append("%s line %d: skipped, %d fields instead of %d" % (os.path.basename(path), i, len(parts), len(COLS)))
            continue
        parts = parts[:len(COLS) - 1] + [" | ".join(parts[len(COLS) - 1:])]
        r = dict(zip(COLS, parts))
        check(path, i, r)
        owner = re.search(r"instagram\.com/([^/]+)/", r["url"]).group(1)
        posts.append({
            "code": code_of(r["url"]), "url": r["url"], "date": r["date"], "hour": r["hour"], "format": r["format"],
            "likes": num(r["likes"]), "likes_hidden": r["likes"].lower() == "hidden",
            "comments": num(r["comments"]), "views": num(r["views"]),
            "slides": num(r["slides"]), "seconds": num(r["seconds"]), "hashtags": num(r["hashtags"]),
            "owner": owner, "partners": r["collab"], "visual": re.sub(r"\s*\(.*\)$", "", re.sub(r"^other \((.*)\)$", r"\1", r["visual"])),
            "topic": r["topic"], "cta": r["cta"] not in ("none", ""), "caption": r["caption"],
        })
    hc = re.search(r"(\d+) posts read", txt)
    if hc and int(hc.group(1)) != len(posts):
        WARN.append("%s: header says %s posts, %d loaded" % (os.path.basename(path), hc.group(1), len(posts)))
    return profile, posts


def main():
    analysis_path = os.path.join(HERE, "analysis.json")
    analysis = json.load(io.open(analysis_path, encoding="utf-8")) if os.path.exists(analysis_path) else {}
    out, last = [], None
    for acc in ACCOUNTS:
        a = dict(acc, readings=[], posts=[], analysis=analysis.get(acc["handle"]))
        by_code = {}
        for path in sorted(glob.glob(os.path.join(HERE, "readings", "*-%s.md" % acc["handle"]))):
            day = os.path.basename(path)[:10]
            profile, posts = parse(path)
            a["readings"].append(dict(profile, date=day))
            seen = set()
            for p in posts:
                p["collab"] = p["owner"] != acc["handle"]
                p["paid"] = p["partners"].lower().startswith("paid partnership")
                by_code[p["code"]] = p
                seen.add(p["code"])
            # A post an older reading had, inside the window this reading covers, but missing now: deleted or unshared.
            lo = profile.get("scope_from", SCOPE_START)
            for c in [c for c, p in by_code.items() if c not in seen and lo <= p["date"] <= day]:
                WARN.append("%s: %s (%s) no longer on the profile, dropped" % (os.path.basename(path), c, by_code[c]["date"]))
                del by_code[c]
            last = max(last or day, day)
        a["last_reading"] = a["readings"][-1]["date"] if a["readings"] else None
        a["coverage_start"] = min([r["scope_from"] for r in a["readings"] if r.get("scope_from")] or [SCOPE_START])
        a["posts"] = sorted(by_code.values(), key=lambda p: p["date"], reverse=True)
        out.append(a)
    as_of = analysis.get("_as_of")
    if not as_of or as_of < last:
        WARN.append("analysis.json was written on %s, the newest reading is %s: rewrite the analysis before publishing" % (as_of, last))
    data = {"scope_start": SCOPE_START, "last_reading": last, "analysis_as_of": as_of, "overall": analysis.get("_overall"), "accounts": out}
    io.open(os.path.join(HERE, "data.js"), "w", encoding="utf-8", newline="\n").write(
        "window.TRACKER_DATA = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n")
    for a in out:
        print("%-22s readings %d  posts %d  last %s  from %s" % (a["handle"], len(a["readings"]), len(a["posts"]), a["last_reading"], a["coverage_start"]))
    for w in WARN:
        print("WARNING", w)
    if not WARN:
        print("All readings loaded clean.")


if __name__ == "__main__":
    main()
