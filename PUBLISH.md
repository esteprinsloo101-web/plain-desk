# Publish Plain Desk to GitHub Pages

**Blocker on authoring box (2026-09-06):** `gh` is **not logged in** (`gh auth status` fails). No `GH_TOKEN` / `GITHUB_TOKEN` in the environment. Public API: `esteprinsloo101-web/judgment-os` exists (200); `esteprinsloo101-web/plain-desk` does **not** yet (404).

**Target:** same publisher as Judgment OS / AEGIS → `https://github.com/esteprinsloo101-web/plain-desk`  
**Live URL:** `https://esteprinsloo101-web.github.io/plain-desk/`

Zip of this site: `/workspace/plain-desk-site.zip`

---

## Option 1 — `gh` (recommended, once authenticated)

Run from a machine where you can log in as `esteprinsloo101-web`:

```bash
gh auth login
# or: export GH_TOKEN=... with repo + pages scope

cd /path/to/plain-desk-site   # or unzip plain-desk-site.zip

# Create private or public repo under the same org/user as judgment-os
gh repo create esteprinsloo101-web/plain-desk --public --source=. --remote=origin --push --description "Plain Desk — SA stokvel / treasurer SEO microsite"

# Enable GitHub Pages from root of main
gh api -X POST "repos/esteprinsloo101-web/plain-desk/pages" \
  -f build_type=legacy \
  -f source[branch]=main \
  -f source[path]=/

# Or via UI: Settings → Pages → Deploy from branch → main → / (root)
```

If the repo already exists empty:

```bash
git init
git checkout -b main
git add index.html styles.css robots.txt sitemap.xml blog .nojekyll README.md
# optional: keep _build.py PUBLISH.md out of public site, or include them
git commit -m "Initial Plain Desk GitHub Pages site"
git remote add origin https://github.com/esteprinsloo101-web/plain-desk.git
git push -u origin main
# then enable Pages as above
```

Wait 1–2 minutes, then open:

- https://esteprinsloo101-web.github.io/plain-desk/
- https://esteprinsloo101-web.github.io/plain-desk/blog/stokvel-constitution-vs-treasurer-pack.html

---

## Option 2 — GitHub web UI

1. Unzip `plain-desk-site.zip`.
2. github.com/new → Owner **esteprinsloo101-web** → Repository name **plain-desk** → Public.
3. Upload: `index.html`, `styles.css`, `robots.txt`, `sitemap.xml`, `.nojekyll`, `blog/` (all five HTML files), `README.md`.
4. Settings → Pages → Branch **main** → Folder **/ (root)** → Save.

---

## Files to publish (root)

| Path | Role |
|------|------|
| `index.html` | Home |
| `styles.css` | CSS |
| `robots.txt` | Crawlers |
| `sitemap.xml` | Sitemap (canonical Pages base) |
| `.nojekyll` | Disable Jekyll processing |
| `blog/*.html` | Five articles |
| `README.md` | Repo readme |

Optional (dev only): `_build.py`, `PUBLISH.md` — safe to omit from Pages.

---

## After go-live

- Confirm CTA still points to https://stofficial.gumroad.com/l/ydbgne
- Submit sitemap in Search Console when ready: `https://esteprinsloo101-web.github.io/plain-desk/sitemap.xml`
- Do **not** cross-link Judgment OS / AEGIS / RandRadar from this site
