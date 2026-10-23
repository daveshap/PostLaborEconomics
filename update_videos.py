#!/usr/bin/env python3
"""Keep the Videos page (docs/videos/) in step with the YouTube playlist.

Reads the playlist's public web page and feed, so no API key is needed, and keeps three things:
  docs/assets/data/videos.json        the list of videos, which the page is built from
  docs/assets/thumbs/videos/*.webp    two thumbnails per video, so the page loads nothing from YouTube until play
  docs/_includes/pages/videos.html    the body of the Videos page
Files change only when the playlist does. Nothing is ever deleted: a video that leaves the playlist
leaves the page, but its thumbnails stay in the repository.

The GitHub Action .github/workflows/update-videos.yml runs this every six hours and commits any change.
To run it by hand (it needs Pillow: pip install pillow):
  python update_videos.py              fetch the playlist and update the files
  python update_videos.py --offline    rebuild the page from videos.json, without fetching anything
"""
import argparse
import datetime
import html
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

PLAYLIST = "PLOa9UVE_V0oI"
FEED_LIMIT = 15        # a YouTube feed lists at most the first 15 videos
PAGE_LIMIT = 100       # the playlist page lists at most the first 100
DATA = "docs/assets/data/videos.json"
THUMBS = "docs/assets/thumbs/videos"
BODY = "docs/_includes/pages/videos.html"
SIZES = (640, 1280)
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9"}
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}")
CHANNEL_ID = re.compile(r"UC[A-Za-z0-9_-]{22}")
DAY = re.compile(r"\d{4}-\d{2}-\d{2}")
LENGTH = re.compile(r"(?:(\d+):)?(\d{1,2}):(\d{2})")
GONE = {"[Private video]", "[Deleted video]"}
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December")
E = html.escape


# ---------------------------------------------------------------- reading ---
def fetch(url, tries=3):
    """GET a URL, retrying network errors. A 404 is raised at once."""
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404 or i == tries - 1:
                raise
        except OSError:
            if i == tries - 1:
                raise
        time.sleep(5 * (i + 1))


def read_feed(url):
    """A YouTube feed: its title, its channel and its videos in feed order, [{id, title, published}]."""
    root = ET.fromstring(fetch(url))
    videos = []
    for e in root.findall("a:entry", NS):
        vid = e.findtext("yt:videoId", "", NS)
        day = e.findtext("a:published", "", NS)[:10]
        if VIDEO_ID.fullmatch(vid):
            videos.append({"id": vid, "title": e.findtext("a:title", "", NS).strip(),
                           "published": day if DAY.fullmatch(day) else ""})
    channel = root.findtext("yt:channelId", "", NS) or root.findtext("a:entry/yt:channelId", "", NS)
    return {"title": root.findtext("a:title", "", NS).strip(), "videos": videos,
            "channel": channel if CHANNEL_ID.fullmatch(channel) else ""}


def find(o, key):
    """Every value stored under `key` anywhere in a JSON tree, in document order."""
    if isinstance(o, dict):
        for k, v in o.items():
            if k == key:
                yield v
            yield from find(v, key)
    elif isinstance(o, list):
        for v in o:
            yield from find(v, key)


def read_page():
    """The playlist page: its videos in playlist order, [{id, title, length}], and whether the list goes on."""
    text = fetch(f"https://www.youtube.com/playlist?list={PLAYLIST}").decode("utf-8", "replace")
    m = re.search(r"""(?:var ytInitialData|window\[["']ytInitialData["']\])\s*=\s*""", text)
    if not m:
        raise ValueError("the playlist page has no ytInitialData")
    data, _ = json.JSONDecoder().raw_decode(text, m.end())
    root = next(find(data, "playlistVideoListRenderer"), data)
    videos, seen = [], set()

    def add(vid, title, length):
        if VIDEO_ID.fullmatch(str(vid)) and vid not in seen and title.strip() and title.strip() not in GONE:
            seen.add(vid)
            videos.append({"id": vid, "title": title.strip(), "length": length if LENGTH.fullmatch(length) else ""})

    def walk(o):
        if isinstance(o, dict):
            r = o.get("playlistVideoRenderer")                       # the older page layout
            if isinstance(r, dict):
                t = r.get("title", {})
                add(r.get("videoId", ""), "".join(x.get("text", "") for x in t.get("runs", [])) or t.get("simpleText", ""),
                    (r.get("lengthText") or {}).get("simpleText", ""))
                return
            r = o.get("lockupViewModel")                             # the current page layout
            if isinstance(r, dict) and r.get("contentType") == "LOCKUP_CONTENT_TYPE_VIDEO":
                title = r.get("metadata", {}).get("lockupMetadataViewModel", {}).get("title", {}).get("content", "")
                badges = [b.get("text", "") for b in find(r, "thumbnailBadgeViewModel") if isinstance(b, dict)]
                add(r.get("contentId", ""), title, next((b for b in badges if LENGTH.fullmatch(b)), ""))
                return
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(root)
    more = next(find(root, "continuationItemRenderer"), None) is not None or len(videos) >= PAGE_LIMIT
    title = next((t for t in find(data, "playlistMetadataRenderer") if isinstance(t, dict)), {}).get("title", "")
    return {"title": title.strip(), "videos": videos, "more": more}


def attempt(what, fn):
    try:
        return fn()
    except Exception as e:                                           # report and carry on with the other source
        print(f"warning: could not read the {what}: {type(e).__name__}: {e}")
        return None


# ---------------------------------------------------------------- merging ---
def merge(old, feed, page, today):
    """The new list of videos. Removals are trusted only when a source shows the whole playlist."""
    fids = [v["id"] for v in feed["videos"]] if feed else []
    pids = [v["id"] for v in page["videos"]] if page else []
    oids = [v["id"] for v in old["videos"]]
    if pids and not page["more"] and set(fids) <= set(pids):
        members, how = pids, "the playlist page"
    elif feed and fids and len(fids) < FEED_LIMIT:
        members, how = fids, "the playlist feed"
    else:
        members = oids + [i for i in pids + fids if i not in oids]
        members, how = list(dict.fromkeys(members)), "the saved list plus what YouTube showed (nothing removed)"
    known = {v["id"]: v for v in old["videos"]}
    by_feed = {v["id"]: v for v in feed["videos"]} if feed else {}
    by_page = {v["id"]: v for v in page["videos"]} if page else {}
    videos = []
    for pos, vid in enumerate(members):
        o, f, p = known.get(vid, {}), by_feed.get(vid, {}), by_page.get(vid, {})
        title = f.get("title") or p.get("title") or o.get("title") or ""
        if title and title not in GONE:
            videos.append({"id": vid, "title": title, "published": f.get("published") or o.get("published") or "",
                           "length": p.get("length") or o.get("length") or "", "added": o.get("added") or today,
                           "_pos": pos})
    return videos, how


def fill_dates(videos, channel):
    """Publish dates the playlist feed lacked, from the channel's own feed (its 15 newest uploads)."""
    if not channel or all(v["published"] for v in videos):
        return
    feed = attempt("channel feed", lambda: read_feed(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel}"))
    days = {v["id"]: v["published"] for v in feed["videos"]} if feed else {}
    for v in videos:
        v["published"] = v["published"] or days.get(v["id"], "")


# ------------------------------------------------------------- thumbnails ---
def thumb_name(vid):
    """The thumbnail file name for a video. Jekyll leaves out files whose names start with an underscore, and
    video IDs can, so those get a "v" in front."""
    return "v" + vid if vid.startswith("_") else vid


def thumbnails(root, vid, offline):
    """Save the video's thumbnail as 16:9 WebP files in two widths, once. True if it saved any."""
    paths = [os.path.join(root, THUMBS, f"{thumb_name(vid)}-{w}.webp") for w in SIZES]
    if all(os.path.exists(p) for p in paths):
        return False
    if offline:
        raise SystemExit(f"error: {vid} has no thumbnails yet; run without --offline")
    from PIL import Image
    for name in ("maxresdefault", "hq720", "sddefault", "hqdefault"):
        try:
            raw = fetch(f"https://i.ytimg.com/vi/{vid}/{name}.jpg")
            break
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
    else:
        raise SystemExit(f"error: YouTube has no thumbnail for {vid}")
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    w, h = im.size
    if abs(w / h - 16 / 9) > 0.02:                                    # 4:3 sizes hold the 16:9 frame between black bars
        keep = round(w * 9 / 16)
        im = im.crop((0, (h - keep) // 2, w, (h - keep) // 2 + keep))
    os.makedirs(os.path.dirname(paths[0]), exist_ok=True)
    for width, path in zip(SIZES, paths):
        im.resize((width, width * 9 // 16), Image.Resampling.LANCZOS).save(path, "WEBP", quality=80, method=6)
    return True


# --------------------------------------------------------------- the page ---
ICON = ('<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true" focusable="false" fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{}</svg>')
EXT = ICON.format('<path d="M7 17 17 7M9 7h8v8"/>')
PLAY = ('<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true" focusable="false" fill="currentColor">'
        '<path d="M8 5.6v12.8a1 1 0 0 0 1.53.85l10.1-6.4a1 1 0 0 0 0-1.7L9.53 4.75A1 1 0 0 0 8 5.6Z"/></svg>')


def nice_day(day):
    y, m, d = (int(x) for x in day.split("-"))
    return f"{MONTHS[m - 1]} {d}, {y}"


def iso_length(text):
    h, m, s = LENGTH.fullmatch(text).groups()
    h, m, s = int(h or 0), int(m), int(s)
    return "PT" + (f"{h}H" if h else "") + (f"{m}M" if m else "") + f"{s}S"


def watch(vid, in_list=True):
    return f"https://www.youtube.com/watch?v={vid}" + (f"&list={PLAYLIST}" if in_list else "")


def day_html(v):
    return f'<time datetime="{v["published"]}">{nice_day(v["published"])}</time>' if v["published"] else ""


def length_html(v):
    return (f'<span class="vh">Length </span><time datetime="{iso_length(v["length"])}" data-len>{E(v["length"])}</time>'
            if v["length"] else "")


def srcset(vid):
    base = f"../assets/thumbs/videos/{thumb_name(vid)}"
    return f'src="{base}-{SIZES[0]}.webp" srcset="{base}-{SIZES[0]}.webp {SIZES[0]}w, {base}-{SIZES[1]}.webp {SIZES[1]}w"'


def card(v):
    lines = ['      <li class="video-card">',
             '        <div class="video-body">',
             f'          <h3><a class="video-link" href="{E(watch(v["id"]))}" data-play="{v["id"]}">{E(v["title"])}</a></h3>']
    if v["published"]:
        lines.append(f'          <p class="video-meta">{day_html(v)}</p>')
    lines += ['        </div>',
              '        <div class="video-thumb">',
              f'          <img {srcset(v["id"])} sizes="(max-width: 560px) 40vw, (max-width: 1080px) 46vw, 380px" '
              'width="640" height="360" alt="" loading="lazy" decoding="async">']
    if v["length"]:
        lines.append(f'          <span class="video-dur">{length_html(v)}</span>')
    lines += ['        </div>', '      </li>']
    return "\n".join(lines)


def render(state):
    videos = state["videos"]
    top = videos[0]
    n = len(videos)
    meta = day_html(top) + (' <span aria-hidden="true">&middot;</span> ' if top["published"] and top["length"] else "") + length_html(top)
    subscribe = (f'https://www.youtube.com/channel/{state["channel"]}?sub_confirmation=1' if state.get("channel")
                 else "https://www.youtube.com/@DaveShap?sub_confirmation=1")
    cards = "\n".join(card(v) for v in videos)
    return f'''<section class="page-hero grid-bg" aria-labelledby="page-title">
  <div class="wrap">
    <p class="eyebrow">Watch</p>
    <h1 id="page-title">Videos</h1>
    <p class="lede">Talks and explainers on post-labor economics from David Shapiro&rsquo;s YouTube channel. This page keeps itself up to date: when a video joins the playlist, it shows up here within a few hours.</p>
    <div class="actions">
      <a class="btn btn-primary" href="{E(f"https://www.youtube.com/playlist?list={PLAYLIST}")}">Open the playlist on YouTube {EXT}</a>
      <a class="btn btn-ghost" href="{E(subscribe)}">Subscribe on YouTube {EXT}</a>
    </div>
  </div>
</section>

<section class="night theater-band" aria-labelledby="now-title">
  <div class="wrap">
    <div class="theater" data-theater data-list="{PLAYLIST}">
      <div class="theater-frame" data-frame>
        <a class="theater-start" href="{E(watch(top["id"]))}" data-play="{top["id"]}">
          <img {srcset(top["id"])} sizes="(max-width: 860px) 92vw, 760px" width="1280" height="720" alt="">
          <span class="play-badge">{PLAY}</span>
          <span class="vh">Play the video: {E(top["title"])}</span>
        </a>
      </div>
      <div class="theater-info">
        <p class="eyebrow" data-label>Latest video</p>
        <h2 id="now-title" data-title>{E(top["title"])}</h2>
        <p class="video-meta" data-meta>{meta}</p>
        <a class="arrow-link" href="{E(watch(top["id"], False))}" data-link>Watch on YouTube {EXT}</a>
        <p class="video-privacy">Videos play from YouTube in its privacy-enhanced mode. Nothing loads from YouTube until you press play.</p>
      </div>
    </div>
  </div>
</section>

<section class="section" aria-labelledby="playlist-title">
  <div class="wrap">
    <div class="section-head">
      <div>
        <p class="eyebrow">The playlist</p>
        <h2 id="playlist-title">{E(state["title"] or "Post-Labor Economics")}</h2>
        <p>{n} video{"" if n == 1 else "s"}, newest first. Updated {nice_day(state["updated"])}.</p>
      </div>
    </div>
    <ul class="video-grid">
{cards}
    </ul>
  </div>
</section>
'''


# ------------------------------------------------------------------- main ---
def write(path, data):
    """Write the file if its content differs. True if it changed."""
    data = data.encode("utf-8") if isinstance(data, str) else data
    if os.path.exists(path) and open(path, "rb").read() == data:
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=os.path.dirname(os.path.abspath(__file__)), help="the repository folder")
    ap.add_argument("--offline", action="store_true", help="rebuild the page from videos.json without fetching")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    today =datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    data_path = os.path.join(args.root, DATA)
    old = (json.load(open(data_path, encoding="utf-8")) if os.path.exists(data_path)
           else {"playlist": PLAYLIST, "title": "", "channel": "", "updated": today, "videos": []})

    if args.offline:
        state = old
    else:
        feed = attempt("playlist feed", lambda: read_feed(f"https://www.youtube.com/feeds/videos.xml?playlist_id={PLAYLIST}"))
        page = attempt("playlist page", read_page)
        if not feed and not page:
            raise SystemExit("error: YouTube could not be read, so nothing was changed")
        videos, how = merge(old, feed, page, today)
        if not videos:
            raise SystemExit("error: the playlist came back empty, so the page was left as it is")
        channel = (feed or {}).get("channel") or old.get("channel", "")
        fill_dates(videos, channel)
        videos.sort(key=lambda v: (v["published"] or v["added"], -v["_pos"]), reverse=True)
        for v in videos:
            del v["_pos"]
        state = {"playlist": PLAYLIST, "title": (feed or {}).get("title") or (page or {}).get("title") or old.get("title", ""),
                 "channel": channel, "updated": old.get("updated", today), "videos": videos}
        same = {k: v for k, v in state.items() if k != "updated"} == {k: v for k, v in old.items() if k != "updated"}
        if not same:
            state["updated"] = today
        added = [v["title"] for v in videos if v["id"] not in {o["id"] for o in old["videos"]}]
        dropped = [o["title"] for o in old["videos"] if o["id"] not in {v["id"] for v in videos}]
        print(f"{len(videos)} videos, from {how}.")
        for t in added:
            print("  new:", t)
        for t in dropped:
            print("  no longer in the playlist:", t)

    if not state["videos"]:
        raise SystemExit("error: videos.json lists no videos")
    changed = []
    for v in state["videos"]:
        if thumbnails(args.root, v["id"], args.offline):
            changed.append(f"{THUMBS}/{thumb_name(v['id'])}-*.webp")
    if write(data_path, json.dumps(state, indent=1, ensure_ascii=False) + "\n"):
        changed.append(DATA)
    if write(os.path.join(args.root, BODY), render(state)):
        changed.append(BODY)
    print("changed:", ", ".join(changed) if changed else "nothing")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(f"changed={'true' if changed else 'false'}\n")


if __name__ == "__main__":
    main()
