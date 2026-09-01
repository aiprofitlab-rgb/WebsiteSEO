import os
import subprocess
from datetime import datetime

public_html = "public_html"
base_url = "https://aiprofitlab.io"

urls = [
    # --- English, the v4 set (launched 2026-08-21) --------------------------
    ("/", 1.0),
    ("/en/services/", 0.9),
    ("/en/process/", 0.8),
    ("/en/about/", 0.8),
    ("/en/contact/", 0.8),
    ("/en/demos/", 0.7),
    ("/en/simulators/", 0.7),
    ("/en/checkout/", 0.7),
    ("/en/smart-storefront/", 0.9),
    ("/blog/", 0.8),

    # --- Arabic, the v4 set (rebuilt 2026-08-21) ----------------------------
    # The five core URLs are unchanged - only the skin under them moved.
    ("/ar/", 0.9),
    ("/services/", 0.8),
    ("/process/", 0.8),
    ("/about/", 0.8),
    ("/contact/", 0.8),
    ("/demos-ar/", 0.7),
    ("/simulators-ar/", 0.7),
    ("/checkout-ar/", 0.7),
    ("/smart-storefront-ar/", 0.9),
    ("/blog-ar/", 0.8),

    # --- Trust pages -------------------------------------------------------
    # Linked from the footer of all 320 pages and never submitted. For a
    # business taking payment online these are trust pages, not boilerplate.
    ("/privacy/", 0.4),
    ("/privacy-ar/", 0.4),
    ("/terms/", 0.4),
    ("/terms-ar/", 0.4),
    ("/refund-policy/", 0.4),
    ("/refund-policy-ar/", 0.4),

    # The Academy is not here on purpose. Its eight pages carry noindex: no
    # live v4 page links to them, they are thin against the articles covering
    # the same ground, and they were competing with them. A sitemap must not
    # advertise a page that tells the crawler not to index it.
    # The two Smart Website offer pages were retired 2026-08-26 and their files
    # deleted 2026-08-27; their URLs 301 to the Smart Storefront campaign
    # (.htaccess section 2). The campaign pages themselves went indexable on
    # 2026-08-27 and ARE listed above, at 0.9: they are the live offer, the
    # only reason they carried noindex was the retired page publishing a rival
    # price for the same build, and that page is gone.
    # Neither /en/order/ nor /order-ar/ belongs here: both are payment-return
    # pages carrying noindex, and /en/checkout/?plan=... are query variants of
    # one URL. The two stand-alone Arabic simulator pages that used to be
    # listed are gone too - they now 301 into /simulators-ar/ (.htaccess
    # section 2c), and a sitemap must not list a URL that redirects.
    # The four stand-alone demo pages came BACK on 2026-08-30, because the
    # homepage proof tiles had never stopped showing their screenshots. They
    # still do not belong here: they carry noindex, follow, and /en/demos/ and
    # /demos-ar/ above are the indexed hubs for the same two demos.
]

blog_ar_path = os.path.join(public_html, "blog", "ar")
if os.path.exists(blog_ar_path):
    for file in os.listdir(blog_ar_path):
        if file.endswith(".html") and file != "index.html":
            slug = file.replace(".html", "")
            urls.append((f"/blog/ar/{slug}/", 0.6))

blog_en_path = os.path.join(public_html, "blog", "en")
if os.path.exists(blog_en_path):
    for file in os.listdir(blog_en_path):
        if file.endswith(".html") and file != "index.html":
            slug = file.replace(".html", "")
            urls.append((f"/blog/en/{slug}/", 0.6))

def source_file(loc):
    """Map a public URL back to the file .htaccess serves for it.

    Mirrors the rewrite rules: /en/<x>/ prefers public_html/en/<x>.html and
    falls back to the older root-level <x>-en.html convention; everything
    else is a root .html file or a directory index.
    """
    path = loc.strip("/")
    if path == "":
        return os.path.join(public_html, "index.html")
    parts = path.split("/")
    candidates = []
    if parts[0] == "en" and len(parts) == 2:
        candidates.append(os.path.join(public_html, "en", parts[1] + ".html"))
        candidates.append(os.path.join(public_html, parts[1] + "-en.html"))
    candidates.append(os.path.join(public_html, *parts) + ".html")
    candidates.append(os.path.join(public_html, *parts, "index.html"))
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


TODAY = datetime.now().strftime("%Y-%m-%d")


def _git_last_modified():
    """Last commit date per file, one `git log` pass.

    mtime is not usable here: a fresh clone or checkout stamps every file with
    the checkout time, which is exactly the uniform-lastmod problem this is
    meant to solve. The commit date is the real one. Files with uncommitted
    edits fall back to today, since they are about to be deployed.
    """
    def git(*args):
        return subprocess.run(("git",) + args, capture_output=True, text=True,
                              check=True, timeout=60).stdout
    try:
        # git reports paths from the repo root, which sits ABOVE this script -
        # without stripping that prefix every lookup misses and every URL
        # silently falls back to today, i.e. the bug this replaces.
        prefix = git("rev-parse", "--show-prefix").strip()
        out = git("log", "--name-only", "--pretty=format:C%cs",
                  "--diff-filter=AMR", "--", public_html)
        st = git("status", "--porcelain", "--", public_html)
    except (OSError, subprocess.SubprocessError):
        return {}, set()

    def strip(path):
        path = path.strip().strip('"')
        return path[len(prefix):] if prefix and path.startswith(prefix) else path

    dates, cur = {}, None
    for line in out.splitlines():
        if line.startswith("C") and len(line) == 11:
            cur = line[1:]
        elif line.strip():
            dates.setdefault(strip(line), cur)    # log is newest-first
    dirty = {strip(l[3:]) for l in st.splitlines() if l[3:].strip()}
    return dates, dirty


GIT_DATES, GIT_DIRTY = _git_last_modified()


def lastmod_for(loc):
    """A uniform lastmod is a signal crawlers learn to discount, which costs
    us the one case where it matters: telling a crawler a page really changed."""
    f = source_file(loc)
    if f is None:
        return TODAY
    key = f.replace(os.sep, "/")
    if key in GIT_DIRTY:
        return TODAY
    return GIT_DATES.get(key) or datetime.fromtimestamp(
        os.path.getmtime(f)).strftime("%Y-%m-%d")


unresolved = []
xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'

for loc, priority in sorted(urls):
    if source_file(loc) is None:
        unresolved.append(loc)
    xml_content += '  <url>\n'
    xml_content += f'    <loc>{base_url}{loc}</loc>\n'
    xml_content += f'    <lastmod>{lastmod_for(loc)}</lastmod>\n'
    xml_content += '    <changefreq>weekly</changefreq>\n'
    xml_content += f'    <priority>{priority}</priority>\n'
    xml_content += '  </url>\n'

xml_content += '</urlset>'

sitemap_file = os.path.join(public_html, "sitemap.xml")
with open(sitemap_file, "w", encoding="utf-8") as f:
    f.write(xml_content)

print(f"SUCCESS: Generated {sitemap_file} with {len(urls)} URLs.")
if unresolved:
    print(f"WARNING: {len(unresolved)} URL(s) have no file on disk - a sitemap"
          " must not list a URL that 404s:")
    for loc in unresolved:
        print("  " + loc)
