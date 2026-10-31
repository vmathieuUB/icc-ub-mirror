#!/usr/bin/env python3
"""Rebuild a static mirror of icc.ub.edu from the Wayback Machine.

Usage: python3 mirror.py OUT_DIR [TIMESTAMP] [MAX_PAGES]
Stdlib only. Downloads raw captures (id_ URLs), rewrites site links to
relative paths, and adds an "unofficial archived mirror" banner.
"""
import collections, gzip, hashlib, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request, posixpath, html

HOSTS = {"icc.ub.edu", "www.icc.ub.edu"}
OUT = sys.argv[1]
TS = sys.argv[2] if len(sys.argv) > 2 else None
MAX_PAGES = int(sys.argv[3]) if len(sys.argv) > 3 else 3000
UA = {"User-Agent": "icc-ub-mirror/1.0 (archival copy for ICCUB)"}
CACHE = OUT.rstrip("/") + ".cache"  # raw downloads, so a rerun does not hit the archive again
DELAY = 4.0  # seconds between archive requests; at 1 s the Wayback Machine refuses connections
OLDEST = "2020"  # earlier captures are the previous site, with dead index.php URLs
SAFE = ":/?#[]@!$&'()*+,;=%-._~"  # keep URLs as they are, only escape spaces and the like
MAX_FILE = 50_000_000  # GitHub rejects files over 100 MB
FILE_EXTS = {
    ".html", ".htm", ".css", ".js", ".mjs", ".map", ".json", ".xml", ".txt", ".csv", ".ico", ".png", ".jpg", ".jpeg",
    ".gif", ".svg", ".webp", ".bmp", ".tif", ".tiff", ".woff", ".woff2", ".ttf", ".eot", ".otf", ".pdf", ".doc",
    ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods", ".odp", ".zip", ".gz", ".tar", ".tgz", ".rar", ".7z",
    ".mp3", ".mp4", ".m4v", ".mov", ".avi", ".webm", ".ogg", ".wav", ".tex", ".bib", ".eps", ".ps",
}


def get(url, tries=6):
    for i in range(tries):
        try:
            time.sleep(DELAY)
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read(), r.headers.get("Content-Type", ""), True
        except urllib.error.HTTPError as e:
            if e.code in (403, 404, 410, 451):
                return None, "", True
            # 429 means rate limited, which takes minutes to clear
            time.sleep(120 if e.code == 429 else 2 ** i)
        except Exception as e:
            print("wait", e, flush=True)  # refused connections mean a temporary block
            time.sleep(300)
    return None, "", False


def unzip(data):
    """Some captures are stored gzipped and the raw id_ URL returns them that way."""
    if data[:2] == b"\x1f\x8b":
        try:
            return gzip.decompress(data)
        except (OSError, EOFError):
            pass
    return data


def cached_get(url):
    """Fetch through the cache. Transient failures are not cached, so a rerun retries them."""
    key = os.path.join(CACHE, hashlib.sha1(url.encode()).hexdigest())
    if os.path.exists(key + ".type"):
        with open(key + ".type") as f:
            ctype = f.read()
        if ctype == "MISS":
            return None, ""
        with open(key, "rb") as f:
            return unzip(f.read()), ctype
    data, ctype, final = get(url)
    if not final:
        return None, ""
    os.makedirs(CACHE, exist_ok=True)
    if data is not None:
        with open(key, "wb") as f:
            f.write(data)
    with open(key + ".type", "w") as f:
        f.write(ctype if data is not None else "MISS")
    return (unzip(data) if data is not None else None), ctype


def key(u):
    p = urllib.parse.urlsplit(u)
    return urllib.parse.unquote(p.path or "/") + ("?" + urllib.parse.unquote(p.query) if p.query else "")


def load_index(ts):
    """Newest capture of each site URL at or before ts, as {key: (timestamp, length)}."""
    path = OUT.rstrip("/") + ".cdx.txt"
    if not os.path.exists(path):
        data, _, _ = get("https://web.archive.org/cdx/search/cdx?url=icc.ub.edu&matchType=host"
                         f"&to={ts}&filter=statuscode:200&fl=original,timestamp,length")
        with open(path, "wb") as f:
            f.write(data)
    index = {}
    with open(path, errors="replace") as f:
        for line in f:
            parts = line.split()
            if len(parts) == 3 and parts[1] >= OLDEST and urllib.parse.urlsplit(parts[0]).hostname in HOSTS:
                index[key(parts[0])] = (parts[1], int(parts[2]) if parts[2].isdigit() else 0)
    return index


def priority(dest):
    """Fetch order: pages and styling, then images, then documents."""
    ext = posixpath.splitext(dest)[1].lower()
    if ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".tif", ".tiff"):
        return 1
    if ext in (".html", ".htm", ".css", ".js", ".mjs", ".json", ".woff", ".woff2", ".ttf", ".eot", ".otf", ".ico"):
        return 0
    return 2


def latest_ts():
    data, _, _ = get("https://web.archive.org/cdx/search/cdx?url=icc.ub.edu/"
                     "&output=json&filter=statuscode:200&fl=timestamp,length&limit=-30")
    rows = json.loads(data)[1:]
    # pick the newest capture whose size is not tiny (a broken page is small)
    sizes = sorted(int(r[1]) for r in rows)
    median = sizes[len(sizes) // 2]
    for ts, ln in reversed(rows):
        if int(ln) >= 0.7 * median:
            return ts
    return rows[-1][0]


def local_path(u):
    """Map an icc.ub.edu URL to a file path inside OUT."""
    p = urllib.parse.urlsplit(u)
    path = urllib.parse.unquote(p.path) or "/"
    if path.endswith("/"):
        path += "index.html"
    elif posixpath.splitext(path)[1].lower() not in FILE_EXTS:
        path += "/index.html"  # clean Drupal URL, possibly with a dot in its slug
    if p.query:
        root, ext = posixpath.splitext(path)
        q = re.sub(r"[^A-Za-z0-9._-]", "_", p.query)[:80]
        path = f"{root}__{q}{ext or '.html'}"
    return path.lstrip("/")


def norm(u, base):
    u = html.unescape(u.strip())
    if not u or u.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None
    try:
        a = urllib.parse.urljoin(base, u)
        a = re.sub(r"^https?://web\.archive\.org/web/\d+[a-z_]*/", "", a)
        p = urllib.parse.urlsplit(a)
        if p.scheme not in ("http", "https") or p.hostname not in HOSTS:
            return None
    except ValueError:  # malformed link in page text, such as "[1]"
        return None
    return urllib.parse.urlunsplit(("https", "icc.ub.edu", p.path or "/", p.query, ""))


ATTR = re.compile(r'''(\b(?:href|src|data-src|poster|action)\s*=\s*)(["'])(.*?)\2''', re.I | re.S)
SRCSET = re.compile(r'''(\bsrcset\s*=\s*)(["'])(.*?)\2''', re.I | re.S)
CSSURL = re.compile(r'''url\(\s*(["']?)([^)"']+)\1\s*\)''', re.I)


def rel(from_file, to_url, frag=""):
    target = local_path(to_url)
    r = posixpath.relpath(target, posixpath.dirname(from_file) or ".")
    if r.endswith("index.html") and target.endswith("index.html"):
        r = r[: -len("index.html")] or "./"
    return urllib.parse.quote(r, safe="/._-~") + frag


def main():
    ts = TS or latest_ts()
    print("snapshot", ts, flush=True)
    date = f"{ts[6:8]}/{ts[4:6]}/{ts[0:4]}"
    banner = ('<div style="position:sticky;top:0;z-index:99999;background:#7a1b1b;color:#fff;'
              'font:14px/1.4 sans-serif;padding:8px 12px;text-align:center">'
              f'Unofficial archived mirror of icc.ub.edu, snapshot of {date} '
              f'(from the <a style="color:#fff;text-decoration:underline" '
              f'href="https://web.archive.org/web/{ts}/https://icc.ub.edu/">Internet Archive</a>). '
              'Some pages, forms and search may not work.</div>')
    not_found = ('<!doctype html><meta charset="utf-8"><title>Not in the mirror</title>'
                 '<body style="font:16px/1.5 sans-serif;max-width:40em;margin:3em auto;padding:0 1em">'
                 '<h1>Page not in this mirror</h1><p>This unofficial archived mirror of icc.ub.edu has no copy of '
                 'this page. <a id="w" href="https://web.archive.org/web/' + ts + '/https://icc.ub.edu/">Try the '
                 'Internet Archive</a>.</p><script>document.getElementById("w").href="https://web.archive.org/web/'
                 + ts + '/https://icc.ub.edu"+location.pathname.replace(/^\\/icc-ub-mirror/,"")+location.search'
                 '</script>')
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, ".nojekyll"), "w").close()
    with open(os.path.join(OUT, "404.html"), "w") as f:
        f.write(not_found)
    index = load_index(ts)
    print("index", len(index), "urls", flush=True)
    queues = [collections.deque(["https://icc.ub.edu/"]), collections.deque(), collections.deque()]
    seen = set(queues[0])
    pages = 0
    phase = 0
    while any(queues):
        now = next(i for i, q in enumerate(queues) if q)
        if now != phase:
            print("phase", now, "pages", pages, flush=True)
            phase = now
        u = queues[now].popleft()
        dest = local_path(u)
        capture = index.get(key(u))
        if capture is None or capture[1] > MAX_FILE:
            print("skip", "absent" if capture is None else "large", u, flush=True)
            continue
        fpath = os.path.join(OUT, dest)
        data, ctype = cached_get(f"https://web.archive.org/web/{capture[0]}id_/" + urllib.parse.quote(u, safe=SAFE))
        if data is None:
            print("miss", u, flush=True)
            continue
        is_html = "html" in ctype or dest.endswith(".html")
        is_css = "css" in ctype or dest.endswith(".css")
        found = []

        def sub_url(m_url, keep):
            frag = ""
            if "#" in m_url:
                m_url, frag = m_url.split("#", 1)
                frag = "#" + frag
            t = norm(m_url, u)
            if not t:
                return keep
            found.append(t)
            return rel(dest, t, frag)

        if is_html:
            if pages >= MAX_PAGES:
                continue
            pages += 1
            text = data.decode("utf-8", "replace")
            # these point at duplicate URLs of the same page
            text = re.sub(r'''<link\b[^>]*\brel=["']?(?:canonical|shortlink|revision)\b[^>]*>''', "", text, flags=re.I)
            text = ATTR.sub(lambda m: m.group(1) + m.group(2) + sub_url(m.group(3), m.group(3)) + m.group(2), text)
            text = SRCSET.sub(lambda m: m.group(1) + m.group(2) + ", ".join(
                " ".join([sub_url(p.split()[0], p.split()[0])] + p.split()[1:])
                for p in m.group(3).split(",") if p.split()) + m.group(2), text)
            text = CSSURL.sub(lambda m: "url(" + m.group(1) + sub_url(m.group(2), m.group(2)) + m.group(1) + ")", text)
            text = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + banner, text, count=1, flags=re.I)
            data = text.encode("utf-8")
        elif is_css:
            text = data.decode("utf-8", "replace")
            text = CSSURL.sub(lambda m: "url(" + m.group(1) + sub_url(m.group(2), m.group(2)) + m.group(1) + ")", text)
            data = text.encode("utf-8")
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        with open(fpath, "wb") as f:
            f.write(data)
        for t in found:
            if t not in seen:
                seen.add(t)
                queues[priority(local_path(t))].append(t)
        print(f"ok {pages} {sum(map(len, queues))} {u}", flush=True)
    print("done", pages, "pages,", len(seen), "urls", flush=True)


if __name__ == "__main__":
    main()
