#!/usr/bin/env python3
"""Build Plain Desk static SEO microsite from markdown drafts."""
from __future__ import annotations

import html
import re
from pathlib import Path

CONTENT = Path("/workspace/ops/seo-playbook/content")
OUT = Path("/workspace/plain-desk-site")
BLOG = OUT / "blog"
BASE = "https://esteprinsloo101-web.github.io/plain-desk"
CTA = "https://stofficial.gumroad.com/l/ydbgne"

ARTICLES = [
    {
        "file": "stokvel-constitution-template-vs-treasurer-pack.md",
        "slug": "stokvel-constitution-vs-treasurer-pack",
    },
    {
        "file": "stokvel-spreadsheet-template-south-africa.md",
        "slug": "stokvel-spreadsheet-template-south-africa",
    },
    {
        "file": "burial-society-contribution-sheet.md",
        "slug": "burial-society-contribution-sheet",
    },
    {
        "file": "stokvel-contribution-tracker.md",
        "slug": "stokvel-contribution-tracker",
    },
    {
        "file": "savings-club-template-south-africa.md",
        "slug": "savings-club-template-south-africa",
    },
]


def parse_frontmatter(text: str) -> tuple[dict, str]:
    meta: dict = {}
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            block = text[3:end].strip()
            body = text[end + 3 :].lstrip("\n")
            for line in block.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip().strip('"')
            return meta, body
    return meta, text


def inline(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<a href="\2" rel="noopener">\1</a>',
        s,
    )
    # bare https links on their own (already escaped, so match literal)
    s = re.sub(
        r"(?<![\"'>])(https://[^\s<]+)",
        r'<a href="\1" rel="noopener">\1</a>',
        s,
    )
    return s


def md_to_html(body: str) -> str:
    lines = body.splitlines()
    out: list[str] = []
    i = 0
    in_ul = False
    in_ol = False
    in_table = False
    table_rows: list[list[str]] = []
    in_code = False
    code_buf: list[str] = []
    in_faq = False

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    def flush_table():
        nonlocal in_table, table_rows
        if not table_rows:
            in_table = False
            return
        out.append('<div class="table-wrap"><table>')
        for ri, row in enumerate(table_rows):
            tag = "th" if ri == 0 else "td"
            # skip separator row
            if ri == 1 and all(re.match(r"^:?-+:?$", c.strip()) for c in row):
                continue
            cells = "".join(f"<{tag}>{inline(c.strip())}</{tag}>" for c in row)
            out.append(f"<tr>{cells}</tr>")
        out.append("</table></div>")
        table_rows = []
        in_table = False

    while i < len(lines):
        line = lines[i]

        if line.strip().startswith("```"):
            close_lists()
            if in_table:
                flush_table()
            if not in_code:
                in_code = True
                code_buf = []
            else:
                out.append("<pre><code>" + html.escape("\n".join(code_buf)) + "</code></pre>")
                in_code = False
                code_buf = []
            i += 1
            continue

        if in_code:
            code_buf.append(line)
            i += 1
            continue

        # headings
        m = re.match(r"^(#{1,3})\s+(.+)$", line)
        if m:
            close_lists()
            if in_table:
                flush_table()
            level = len(m.group(1))
            title = m.group(2).strip()
            if title == "FAQ":
                in_faq = True
                out.append('<section class="faq" id="faq">')
                out.append(f"<h{level}>{inline(title)}</h{level}>")
            elif title == "Get the pack":
                if in_faq:
                    out.append("</section>")
                    in_faq = False
                out.append('<section class="cta-block" id="get-the-pack">')
                out.append(f"<h{level}>{inline(title)}</h{level}>")
            else:
                if in_faq and level == 2:
                    out.append("</section>")
                    in_faq = False
                out.append(f"<h{level}>{inline(title)}</h{level}>")
            i += 1
            continue

        # table rows
        if "|" in line and line.strip().startswith("|"):
            close_lists()
            cells = [c for c in line.strip().strip("|").split("|")]
            table_rows.append(cells)
            in_table = True
            i += 1
            # peek: if next isn't table, flush
            if i >= len(lines) or "|" not in lines[i] or not lines[i].strip().startswith("|"):
                flush_table()
            continue

        # checklist
        m = re.match(r"^- \[([ xX])\]\s+(.+)$", line)
        if m:
            if in_table:
                flush_table()
            if in_ol:
                out.append("</ol>")
                in_ol = False
            if not in_ul:
                out.append('<ul class="checklist">')
                in_ul = True
            checked = " checked" if m.group(1).lower() == "x" else ""
            out.append(f"<li><input type=\"checkbox\" disabled{checked}> {inline(m.group(2))}</li>")
            i += 1
            continue

        # unordered list
        m = re.match(r"^[-*]\s+(.+)$", line)
        if m:
            if in_table:
                flush_table()
            if in_ol:
                out.append("</ol>")
                in_ol = False
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{inline(m.group(1))}</li>")
            i += 1
            continue

        # ordered list
        m = re.match(r"^(\d+)\.\s+(.+)$", line)
        if m:
            if in_table:
                flush_table()
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if not in_ol:
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{inline(m.group(2))}</li>")
            i += 1
            continue

        # blank
        if not line.strip():
            close_lists()
            if in_table:
                flush_table()
            i += 1
            continue

        # CTA arrow line → link
        if line.strip().startswith("→"):
            close_lists()
            url = line.strip().lstrip("→").strip()
            out.append(
                f'<p class="cta-link"><a class="btn" href="{html.escape(url)}" rel="noopener">'
                f"Get Stokvel OS — R199</a></p>"
            )
            i += 1
            continue

        # FAQ Q/A pattern: **Q** then next lines as A until blank or next **
        # Already handled as paragraphs with bold
        close_lists()
        if in_table:
            flush_table()

        # Paragraph — FAQ style: line starts with **Question?**
        stripped = line.strip()
        if in_faq and stripped.startswith("**") and stripped.endswith("**"):
            out.append(f'<h3 class="faq-q">{inline(stripped.strip("*"))}</h3>')
            i += 1
            # gather answer until blank or next ** heading-like
            ans = []
            while i < len(lines) and lines[i].strip() and not (
                lines[i].strip().startswith("**") and lines[i].strip().endswith("**")
            ) and not lines[i].startswith("#"):
                ans.append(lines[i].strip())
                i += 1
            if ans:
                out.append(f"<p>{inline(' '.join(ans))}</p>")
            continue

        out.append(f"<p>{inline(stripped)}</p>")
        i += 1

    close_lists()
    if in_table:
        flush_table()
    if in_code:
        out.append("<pre><code>" + html.escape("\n".join(code_buf)) + "</code></pre>")
    if in_faq:
        out.append("</section>")
    # close cta-block if open (heuristic: last section)
    joined = "\n".join(out)
    if '<section class="cta-block"' in joined and joined.count("<section") > joined.count("</section>"):
        joined += "\n</section>"
    return joined


SHELL_HEAD = """<!DOCTYPE html>
<html lang="en-ZA">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title}</title>
<meta name="description" content="{desc}" />
<meta name="robots" content="index,follow" />
<link rel="canonical" href="{canonical}" />
<meta property="og:title" content="{title_esc}" />
<meta property="og:description" content="{desc}" />
<meta property="og:type" content="{ogtype}" />
<meta property="og:url" content="{canonical}" />
<meta name="theme-color" content="#1a5c4a" />
<link rel="stylesheet" href="{css}" />
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="logo" href="{home}">Plain Desk</a>
    <nav aria-label="Primary">
      <a href="{home}#articles">Guides</a>
      <a class="nav-cta" href="{cta}" rel="noopener">Stokvel OS</a>
    </nav>
  </div>
</header>
"""

SHELL_FOOT = """
<footer class="site-footer">
  <div class="wrap">
    <p><strong>Plain Desk</strong> — practical admin templates for South African treasurers and job seekers.</p>
    <p class="fine">Not a bank. Not insurance. Not legal, tax, or financial advice. Not a NASASA filing service. Templates only — you keep the money and the member data.</p>
    <p class="fine"><a href="{cta}" rel="noopener">Stokvel OS on Gumroad</a> · <a href="{home}">Home</a></p>
  </div>
</footer>
</body>
</html>
"""


def article_page(meta: dict, body_html: str, slug: str) -> str:
    title = meta.get("title", "Plain Desk")
    page_title = f"{title} | Plain Desk"
    desc = html.escape(meta.get("meta", ""))
    canonical = f"{BASE}/blog/{slug}.html"
    head = SHELL_HEAD.format(
        title=html.escape(page_title),
        title_esc=html.escape(title),
        desc=desc,
        canonical=canonical,
        ogtype="article",
        css="../styles.css",
        home="../index.html",
        cta=CTA,
    )
    # strip leading H1 from body if present (we show it in hero)
    body_html2 = re.sub(r"^<h1>[^<]+</h1>\s*", "", body_html, count=1)
    # Find first paragraph as lead if present
    main = f"""<main id="main" class="wrap article">
  <p class="eyebrow"><a href="../index.html">Plain Desk</a> · Guide</p>
  <h1>{html.escape(meta.get('title', title))}</h1>
  {body_html2}
  <aside class="cta-card">
    <h2>Plain Desk Stokvel OS</h2>
    <p>Constitution template + member register + contribution tracker + fine/loan log + year-end payout. One-time download for SA stokvels, savings clubs, and burial society bookkeeping.</p>
    <p><a class="btn" href="{CTA}" rel="noopener">Get Stokvel OS — R199</a></p>
    <p class="fine">Not a bank · Not insurance · Not financial advice</p>
  </aside>
</main>
"""
    foot = SHELL_FOOT.format(cta=CTA, home="../index.html")
    return head + main + foot


def index_page(cards: list[dict]) -> str:
    title = "Plain Desk — Stokvel OS & SA treasurer templates"
    desc = html.escape(
        "Faceless SA admin templates. Stokvel OS: constitution + contribution tracker for savings clubs and burial societies. R199 on Gumroad."
    )
    canonical = f"{BASE}/"
    head = SHELL_HEAD.format(
        title=html.escape(title),
        title_esc=html.escape("Plain Desk"),
        desc=desc,
        canonical=canonical,
        ogtype="website",
        css="styles.css",
        home="index.html",
        cta=CTA,
    )
    card_html = []
    for c in cards:
        card_html.append(
            f"""<article class="card">
  <h2><a href="blog/{c['slug']}.html">{html.escape(c['title'])}</a></h2>
  <p>{html.escape(c['meta'])}</p>
  <p><a class="text-link" href="blog/{c['slug']}.html">Read guide →</a></p>
</article>"""
        )
    main = f"""<main id="main">
  <section class="hero wrap">
    <p class="eyebrow">South Africa · Digital downloads</p>
    <h1>Stop running the stokvel from WhatsApp chaos.</h1>
    <p class="lead">Plain Desk builds calm, practical templates for treasurers — constitution wording plus the spreadsheets that keep contributions, members, and year-end payouts visible.</p>
    <p class="hero-actions">
      <a class="btn" href="{CTA}" rel="noopener">Get Stokvel OS — R199</a>
      <a class="btn ghost" href="#articles">Read the guides</a>
    </p>
    <ul class="hero-bullets">
      <li>Adaptable constitution template</li>
      <li>Member register + contribution tracker</li>
      <li>Fine / loan log + year-end payout sheet</li>
      <li>Excel &amp; Google Sheets friendly · instant download</li>
    </ul>
    <p class="fine">Not a bank. Not insurance. Not a NASASA filing service. You keep the money and the member data.</p>
  </section>

  <section class="wrap product" id="stokvel-os">
    <h2>Stokvel OS</h2>
    <p>One treasurer pack for SA savings clubs, grocery stokvels, and burial society <strong>bookkeeping</strong>. Rules on paper; money movements in a ledger you own.</p>
    <p><a class="btn" href="{CTA}" rel="noopener">Buy on Gumroad — R199</a></p>
  </section>

  <section class="wrap articles" id="articles">
    <h2>Guides</h2>
    <p class="section-lead">Free reading for treasurers and secretaries. Each guide ends with the same pack CTA.</p>
    <div class="card-grid">
      {"".join(card_html)}
    </div>
  </section>
</main>
"""
    foot = SHELL_FOOT.format(cta=CTA, home="index.html")
    return head + main + foot


CSS = """/* Plain Desk — clean, faceless, SA treasurer tools */
:root {
  --bg: #f7f5f0;
  --paper: #ffffff;
  --ink: #1a1f1c;
  --muted: #5a655e;
  --line: #e2ddd3;
  --brand: #1a5c4a;
  --brand-ink: #06221a;
  --accent: #c4a574;
  --focus: #0b6e4f;
  --radius: 12px;
  --max: 42rem;
  --wide: 64rem;
  --font: "Segoe UI", system-ui, -apple-system, Roboto, "Helvetica Neue", Arial, sans-serif;
}
*, *::before, *::after { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: var(--font);
  color: var(--ink);
  background: var(--bg);
  line-height: 1.6;
  font-size: 1.05rem;
}
a { color: var(--brand); }
a:hover { color: var(--focus); }
.skip {
  position: absolute; left: -999px; top: 0;
  background: var(--brand); color: #fff; padding: 8px 12px;
}
.skip:focus { left: 8px; z-index: 99; }
.wrap { width: min(100% - 2rem, var(--wide)); margin-inline: auto; }
.article.wrap { width: min(100% - 2rem, var(--max)); }

.site-header {
  background: var(--paper);
  border-bottom: 1px solid var(--line);
  position: sticky; top: 0; z-index: 10;
}
.header-inner {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.85rem 0; gap: 1rem;
}
.logo {
  font-weight: 700; letter-spacing: 0.04em; text-decoration: none;
  color: var(--ink); text-transform: uppercase; font-size: 0.9rem;
}
.logo:hover { color: var(--brand); }
nav { display: flex; gap: 1rem; align-items: center; font-size: 0.95rem; }
nav a { text-decoration: none; color: var(--muted); }
nav a:hover { color: var(--ink); }
.nav-cta {
  background: var(--brand); color: #fff !important;
  padding: 0.4rem 0.85rem; border-radius: 999px; font-weight: 600;
}
.nav-cta:hover { filter: brightness(1.08); }

.btn {
  display: inline-block;
  background: var(--brand); color: #fff !important;
  text-decoration: none; font-weight: 650;
  padding: 0.7rem 1.15rem; border-radius: var(--radius);
  border: 1px solid transparent;
}
.btn:hover { filter: brightness(1.06); }
.btn.ghost {
  background: transparent; color: var(--ink) !important;
  border-color: var(--line);
}

.hero { padding: 2.5rem 0 1.5rem; }
.eyebrow {
  text-transform: uppercase; letter-spacing: 0.1em;
  font-size: 0.75rem; color: var(--muted); margin: 0 0 0.75rem;
}
.eyebrow a { color: inherit; text-decoration: none; }
.eyebrow a:hover { color: var(--brand); }
.hero h1, .article h1 {
  font-size: clamp(1.6rem, 4vw, 2.25rem);
  line-height: 1.2; margin: 0 0 0.85rem; font-weight: 750;
}
.lead { font-size: 1.15rem; color: var(--muted); max-width: 40rem; }
.hero-actions { display: flex; flex-wrap: wrap; gap: 0.75rem; margin: 1.25rem 0; }
.hero-bullets {
  margin: 1.25rem 0; padding-left: 1.2rem; color: var(--ink);
}
.hero-bullets li { margin: 0.35rem 0; }
.fine { font-size: 0.85rem; color: var(--muted); }

.product {
  background: var(--paper); border: 1px solid var(--line);
  border-radius: 16px; padding: 1.5rem 1.5rem 1.35rem; margin: 1rem auto 2rem;
  width: min(100% - 2rem, var(--wide));
}
.product h2 { margin-top: 0; }

.articles { padding-bottom: 3rem; }
.section-lead { color: var(--muted); margin-top: -0.35rem; }
.card-grid {
  display: grid; gap: 1rem;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  margin-top: 1.25rem;
}
.card {
  background: var(--paper); border: 1px solid var(--line);
  border-radius: 14px; padding: 1.15rem 1.2rem;
}
.card h2 { font-size: 1.1rem; margin: 0 0 0.5rem; line-height: 1.35; }
.card h2 a { text-decoration: none; color: var(--ink); }
.card h2 a:hover { color: var(--brand); }
.card p { margin: 0 0 0.65rem; color: var(--muted); font-size: 0.95rem; }
.text-link { font-weight: 600; text-decoration: none; }

.article { padding: 1.75rem 0 3rem; }
.article h2 {
  font-size: 1.35rem; margin: 2rem 0 0.75rem;
  padding-top: 0.5rem; border-top: 1px solid var(--line);
}
.article h2:first-of-type { border-top: 0; padding-top: 0; }
.article h3 { font-size: 1.1rem; margin: 1.35rem 0 0.5rem; }
.article p { margin: 0 0 1rem; }
.article ul, .article ol { margin: 0 0 1rem; padding-left: 1.35rem; }
.article li { margin: 0.3rem 0; }
.checklist { list-style: none; padding-left: 0; }
.checklist li { display: flex; gap: 0.5rem; align-items: flex-start; }
.checklist input { margin-top: 0.35rem; }

.table-wrap { overflow-x: auto; margin: 0 0 1.25rem; }
table {
  width: 100%; border-collapse: collapse; font-size: 0.95rem;
  background: var(--paper);
}
th, td {
  border: 1px solid var(--line); padding: 0.55rem 0.7rem;
  text-align: left; vertical-align: top;
}
th { background: #eef3f0; font-weight: 650; }

pre {
  background: #1a1f1c; color: #e8efe9; padding: 1rem;
  border-radius: 10px; overflow-x: auto; font-size: 0.85rem;
}
code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.9em; }
p code, li code, td code {
  background: #eef3f0; padding: 0.1em 0.35em; border-radius: 4px;
}
pre code { background: transparent; padding: 0; }

.faq { margin: 2rem 0; }
.faq-q { font-size: 1.05rem; margin: 1.25rem 0 0.35rem; }
.cta-block { margin: 1.5rem 0; }
.cta-link { margin: 1rem 0; }

.cta-card {
  margin-top: 2.5rem; padding: 1.35rem 1.4rem;
  background: #eef6f2; border: 1px solid #c5ddd2;
  border-radius: 14px;
}
.cta-card h2 { margin: 0 0 0.5rem; border: 0; padding: 0; font-size: 1.2rem; }

.site-footer {
  border-top: 1px solid var(--line); background: var(--paper);
  padding: 1.75rem 0 2.25rem; margin-top: 1rem;
}
.site-footer p { margin: 0 0 0.5rem; color: var(--muted); font-size: 0.95rem; }
.site-footer strong { color: var(--ink); }

@media (max-width: 520px) {
  .hero-actions { flex-direction: column; align-items: stretch; }
  .btn { text-align: center; }
}
"""


def robots_txt() -> str:
    return f"""User-agent: *
Allow: /

Sitemap: {BASE}/sitemap.xml
"""


def sitemap_xml(slugs: list[str]) -> str:
    urls = [f"  <url><loc>{BASE}/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>"]
    for s in slugs:
        urls.append(
            f"  <url><loc>{BASE}/blog/{s}.html</loc><changefreq>monthly</changefreq><priority>0.8</priority></url>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )


def main():
    BLOG.mkdir(parents=True, exist_ok=True)
    cards = []
    slugs = []
    for a in ARTICLES:
        raw = (CONTENT / a["file"]).read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)
        body_html = md_to_html(body)
        page = article_page(meta, body_html, a["slug"])
        path = BLOG / f"{a['slug']}.html"
        path.write_text(page, encoding="utf-8")
        print(f"wrote {path}")
        cards.append({"slug": a["slug"], "title": meta.get("title", a["slug"]), "meta": meta.get("meta", "")})
        slugs.append(a["slug"])

    (OUT / "index.html").write_text(index_page(cards), encoding="utf-8")
    (OUT / "styles.css").write_text(CSS, encoding="utf-8")
    (OUT / "robots.txt").write_text(robots_txt(), encoding="utf-8")
    (OUT / "sitemap.xml").write_text(sitemap_xml(slugs), encoding="utf-8")
    print("wrote index, styles, robots, sitemap")


if __name__ == "__main__":
    main()
