#!/usr/bin/env python3
"""Rebuild a static mirror of icc.ub.edu from the Wayback Machine.

Usage: python3 mirror.py OUT_DIR [TIMESTAMP] [MAX_PAGES]
Stdlib only. Downloads raw captures (id_ URLs), rewrites site links to
relative paths, and adds an "unofficial archived mirror" banner.
"""
import json, os, re, sys, time, urllib.parse, urllib.request, posixpath, html

HOSTS = {"icc.ub.edu", "www.icc.ub.edu"}
OUT = sys.argv[1]
TS = sys.argv[2] if len(sys.argv) > 2 else None
MAX_PAGES = int(sys.argv[3]) if len(sys.argv) > 3 else 3000
UA = {"User-Agent": "icc-ub-mirror/1.0 (archival copy for ICCUB)"}


def get(url, tries=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read(), r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            if e.code in (404, 403):
                return None, ""
            time.sleep(2 ** i)
        except Exception:
            time.sleep(2 ** i)
    return None, ""


def latest_ts():
    data, _ = get("https://web.archive.org/cdx/search/cdx?url=icc.ub.edu/"
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
    elif "." not in posixpath.basename(path):
        path += "/index.html"
    if p.query:
        root, ext = posixpath.splitext(path)
        q = re.sub(r"[^A-Za-z0-9._-]", "_", p.query)[:80]
        path = f"{root}__{q}{ext or '.html'}"
    return path.lstrip("/")


def norm(u, base):
    u = html.unescape(u.strip())
    if not u or u.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None
    a = urllib.parse.urljoin(base, u)
    a = re.sub(r"^https?://web\.archive\.org/web/\d+[a-z_]*/", "", a)
    p = urllib.parse.urlsplit(a)
    if p.scheme not in ("http", "https") or p.hostname not in HOSTS:
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
    return r + frag


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
    queue = ["https://icc.ub.edu/"]
    seen = set(queue)
    pages = 0
    while queue:
        u = queue.pop(0)
        dest = local_path(u)
        fpath = os.path.join(OUT, dest)
        data, ctype = get(f"https://web.archive.org/web/{ts}id_/{u}")
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
                queue.append(t)
        print(f"ok {pages} {len(queue)} {u}", flush=True)
    open(os.path.join(OUT, ".nojekyll"), "w").close()
    print("done", pages, "pages,", len(seen), "urls", flush=True)


if __name__ == "__main__":
    main()
