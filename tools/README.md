# tools

Small build-time checks for the site. Standard library Python only — no installs.

## link_lint.py — internal-link gap checker

Catches the bug the site's link audit found: inside an **enumeration** (a table
cell, or a comma/middot-separated list of methods) that already links one method,
a sibling method that has its own page is left as plain text — the "one linked,
its neighbour plain" pattern (e.g. `gradient boosting` linked but `boosting`
plain in the next row).

It is scoped to enumerations on purpose, so ordinary prose mentions of a concept
are **not** flagged — only lists where a peer is already linked. That keeps it
high-signal instead of nagging about every repeat of "GARCH".

```bash
python tools/link_lint.py                 # scan the whole site, print candidates
python tools/link_lint.py --strict        # exit 1 if any candidates (for CI/gating)
python tools/link_lint.py phd/index.qmd   # scan specific files
```

Output is `file : line : 'term' is plain text but has a page -> url`. These are
*candidates*, not errors — link them, or leave them if the plain mention is
deliberate. Run it in the same pass that verifies the site's numbers.

### link_map.json — the canonical term → URL map

The source of truth for which terms map to which entry. Each record:

```json
{ "url": "ml/xgboost/", "qmd": "ml/xgboost/index.qmd",
  "aliases": ["gradient boosting", "boosting", "XGBoost"] }
```

- `url` — the path fragment as it appears inside links (`../ml/xgboost/index.qmd`
  contains `ml/xgboost/`).
- `qmd` — the entry's own source, skipped so it is never flagged on its own page.
- `aliases` — the terms (including two-names-one-concept cases like
  `gradient boosting` / `boosting`) that should resolve to this entry.

Add an entry here whenever you publish a new page, and add aliases when a concept
picks up a second name — that is what closes the "same concept, two names, one
link" class of bug for good.
