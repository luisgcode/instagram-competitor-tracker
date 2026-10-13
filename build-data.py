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


def parse(path):
    txt = io.open(path, encoding="utf-8").read()
    m = re.search(r"([\d,]+)\s+followers\s*\|\s*([\d,]+)\s+following\s*\|\s*([\d,]+)\s+posts", txt)
    profile = {"followers": num(m.group(1)), "following": num(m.group(2)), "posts_total": num(m.group(3))} if m else {}
    posts = []
    block = re.search(r"```\n(.*?)```", txt, re.S)
    for line in (block.group(1).splitlines() if block else []):
        parts = [p.strip() for p in line.split(" | ")]
        if len(parts) < len(COLS) or not parts[0].startswith("http"):
            continue
        parts = parts[:len(COLS) - 1] + [" | ".join(parts[len(COLS) - 1:])]
        r = dict(zip(COLS, parts))
        owner = re.search(r"instagram\.com/([^/]+)/", r["url"]).group(1)
        posts.append({
            "url": r["url"], "date": r["date"], "hour": r["hour"], "format": r["format"],
            "likes": num(r["likes"]), "likes_hidden": r["likes"].lower() == "hidden",
            "comments": num(r["comments"]), "views": num(r["views"]),
            "slides": num(r["slides"]), "seconds": num(r["seconds"]), "hashtags": num(r["hashtags"]),
            "owner": owner, "partners": r["collab"], "visual": re.sub(r"\s*\(.*\)$", "", re.sub(r"^other \((.*)\)$", r"\1", r["visual"])),
            "topic": r["topic"], "cta": r["cta"] not in ("none", ""), "caption": r["caption"],
        })
    return profile, posts


def main():
    analysis_path = os.path.join(HERE, "analysis.json")
    analysis = json.load(io.open(analysis_path, encoding="utf-8")) if os.path.exists(analysis_path) else {}
    out, last = [], None
    for acc in ACCOUNTS:
        a = dict(acc, readings=[], posts=[], analysis=analysis.get(acc["handle"]))
        by_url = {}
        for path in sorted(glob.glob(os.path.join(HERE, "readings", "*-%s.md" % acc["handle"]))):
            day = os.path.basename(path)[:10]
            profile, posts = parse(path)
            a["readings"].append(dict(profile, date=day))
            for p in posts:
                p["collab"] = p["owner"] != acc["handle"]
                p["paid"] = p["partners"].lower().startswith("paid partnership")
                by_url[p["url"]] = p
            last = max(last or day, day)
        a["posts"] = sorted(by_url.values(), key=lambda p: p["date"], reverse=True)
        out.append(a)
    data = {"scope_start": SCOPE_START, "last_reading": last, "overall": analysis.get("_overall"), "accounts": out}
    io.open(os.path.join(HERE, "data.js"), "w", encoding="utf-8", newline="\n").write(
        "window.TRACKER_DATA = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n")
    for a in out:
        print("%-22s readings %d  posts %d" % (a["handle"], len(a["readings"]), len(a["posts"])))


if __name__ == "__main__":
    main()
