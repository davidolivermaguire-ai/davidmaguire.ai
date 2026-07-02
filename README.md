# davidmaguire.ai

Personal quant research site — an open lab notebook of research write-ups and
reading notes. Built with [Quarto](https://quarto.org); static HTML output, no
server. Code chunks in posts are shown but **not executed at build time**
(figures are pre-generated and committed), so the site builds with only Quarto
installed — no Python needed in CI.

## Structure

```
_quarto.yml          site config, nav, theme, math renderer
index.qmd            landing page + featured listings
research.qmd         listing of research posts
notes.qmd            listing of reading notes
about.qmd            bio + research interests  (edit the [PLACEHOLDERS])
research/<slug>/index.qmd    one folder per research post (+ its figures)
notes/<slug>/index.qmd       one folder per reading note
code/                standalone, reproducible scripts referenced by posts
styles/theme.scss    visual theme
assets/favicon.svg
```

## Local preview

Install Quarto (https://quarto.org/docs/get-started/), then:

```bash
quarto preview      # live-reloading local server
quarto render       # build static site into _site/
```

## Add a research post

1. `mkdir research/my-new-idea` and create `research/my-new-idea/index.qmd`.
2. Front matter:
   ```yaml
   ---
   title: "Title"
   description: "One-sentence summary for the listing and social preview."
   date: 2026-07-01
   author: "David Maguire"
   categories: [tag1, tag2]
   image: fig-1.png        # optional card image, lives in the same folder
   ---
   ```
3. Write. Maths uses LaTeX: inline `$...$`, display `$$...$$` (rendered with
   KaTeX). Show code with fenced ```` ```python ```` blocks and commit any
   figures next to the `.qmd`. It appears on the Research page automatically.

A reading note is the same, under `notes/<slug>/`.

## Deploy — free options

### Option A · GitHub Pages (recommended, fully free, no build config to babysit)

1. Push this folder to a GitHub repo (e.g. `davidolivermaguire-ai/davidmaguire.ai`) on `main`.
   Replace every `davidolivermaguire-ai` placeholder first (`_quarto.yml`, the post footer link).
2. Repo **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. The included workflow (`.github/workflows/publish.yml`) renders with Quarto
   and deploys on every push to `main`.
4. **Custom domain:** the `CNAME` file already contains `davidmaguire.ai`. Enter
   the same domain under Settings → Pages → Custom domain, and tick *Enforce
   HTTPS* once the certificate is issued.

**DNS at your .ai registrar** (apex domain → GitHub Pages):

| Type  | Host / Name | Value |
|-------|-------------|-------|
| A     | @           | 185.199.108.153 |
| A     | @           | 185.199.109.153 |
| A     | @           | 185.199.110.153 |
| A     | @           | 185.199.111.153 |
| CNAME | www         | davidolivermaguire-ai.github.io |

(Verify these against GitHub's current docs — the Pages IPs are stable but worth
a check. `.ai` DNS changes can take a few hours to propagate.)

### Option B · Cloudflare Pages or Netlify

Both have free tiers and deploy straight from the repo. Quarto isn't on their
build images, so `netlify.toml` + `netlify-build.sh` install it, then run
`quarto render` with publish directory `_site`. On Cloudflare Pages, set the
build command to `bash netlify-build.sh` and output directory to `_site`. Add the
custom domain in the dashboard.

## Before you publish — a content checklist

- [ ] Replaced every `[PLACEHOLDER]` and `davidolivermaguire-ai`.
- [ ] Depth over breadth: a couple of genuinely worked pieces beat many stubs.
- [ ] Every data-driven claim has committed, runnable code.
- [ ] No employer / NDA-covered IP anywhere.
- [ ] No overclaimed "alpha" — frame as research and learning.
- [ ] The maths is correct. Reread it.
