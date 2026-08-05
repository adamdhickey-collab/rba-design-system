# Icons

**1,490 icons in 80 packs.** One outline weight, drawn on a 64×64 grid at a 2px
stroke. Every icon exists twice: an SVG and a 267×267 transparent PNG.

```
assets/icons/
├── ai-finance/
│   ├── ai-finance-01.svg
│   ├── ai-finance-01.png
│   └── … 16 icons
├── audit/
└── … 78 more packs
```

This folder is **generated**. Do not add files to it by hand — they will be
deleted the next time anyone runs the sync script.

## Adding a pack

1. Unzip the pack into `icons/` at the repo root, keeping the folder name the
   drop came with (`<name>-outline-icons-<date>-utc`, holding `svg/` and `png/`).
2. Add it to the `PACKS` table in `tools/icons-sync.py` with a display name, one
   of the eight groups, and search keywords. The script **fails** on a pack that
   isn't in that table rather than filing it under nothing.
3. Run the sync, then rebuild the bundles:

```bash
./tools/icons-sync.py && ./tools/build-bundles.sh
```

Commit `assets/icons/`, `icons.html`, `downloads/` and `app.js` together.

`icons/` itself is gitignored: 124 MB of it is Illustrator and EPS sources that
nobody downloading an icon from a web page will open. **It is not backed up by
this repository** — keep the original download somewhere safe, because it is the
only copy of the vector sources.

To check the manifest still matches what is staged, without writing anything:

```bash
./tools/icons-sync.py --check
```

## Giving icons real names

`Finance-04` tells you nothing, which is the biggest weakness of the library as
it stands. Search papers over it by matching each pack's keywords, so *invoice*
and *chart* and *hiring* find something today — but that is a whole pack at a
time, not the one icon someone wants.

Real names go in the manifest, not in filenames. Each pack takes an optional
`labels` map of icon number to name:

```json
{ "slug": "finance", "name": "Finance", "count": 30, "labels": { "04": "invoice-paid", "11": "piggy-bank" } }
```

A label replaces the displayed name everywhere and joins the search haystack
**alongside** the old one, so someone who knows it as `Finance-04` still finds it
after it is renamed. No file moves, no link breaks, no bundle rebuild.

The sync script reads the existing manifest out of `icons.html` before it
rewrites it, so **labels survive a re-sync** — that is the single guarantee the
script is built around. A label pointing at an icon that no longer exists is
dropped. Naming a pack at a time is the practical unit of work; there is no need
to do all 1,490 before any of it is useful.

## File requirements

Only relevant if you are hand-preparing a pack rather than dropping a purchased
one:

- **64×64 viewBox**, 2px stroke, `stroke-linecap` and `stroke-linejoin` round.
- One numbering sequence per pack: `<Name>-01` … `<Name>-NN`, no gaps.
- **Every SVG needs a matching PNG.** Every tile offers both formats, so a
  missing PNG ships a download button pointing at a 404. The sync script refuses
  the pack rather than staging a half-set.

Filenames are normalised on the way in — `IT Administrator-14.svg` becomes
`it-administrator-14.svg`. 332 of the source files contain spaces and the
capitalisation varies per pack; serving that verbatim means percent-encoded URLs
and case bugs that only appear on Linux hosting. The original casing is not lost,
it is the pack's `name` in the manifest, which is what you see and what search
matches.

## Why the icons follow the theme

They're painted as a CSS **mask**, not an `<img>`. An `<img>` renders the file's
own colors and cannot inherit `currentColor`, so a single monochrome file could
never follow the theme — dark mode would need a second copy of all 1,490. The
mask paints the file's alpha channel with the tile's color instead.

The practical consequence: **the near-black stroke inside each file is ignored on
this site** but is exactly what you get if you download the file and drop it into
a slide. On a dark background you will need to recolor it, or mask it the same
way this site does.

## Why the grid doesn't fetch 1,490 files

An `IntersectionObserver` sets each tile's mask URL only as it nears the
viewport. Opening the page costs about 40 requests, not 1,490. Filtering hides
tiles rather than rebuilding them, because re-creating 13,000 nodes on every
keystroke is not free.

## Copy SVG needs a served page

The copy button fetches the file, which the browser blocks on a `file://` page.
The buttons remove themselves when the page isn't served over http — the SVG and
PNG download links still work. Serve the folder if you need copy:

```bash
python3 -m http.server 3477
```

## Licensing

These are purchased stock packs (credited `Upnowgraphic`), and the drop carries
no licence file — only a `readme.txt` listing what's in the box. Most stock icon
licences permit use in work product but **not** redistribution of the assets
themselves as standalone downloads, which is exactly what this page does.

That is fine behind RBA's login. It is worth a second look while this repository
is public. Whoever purchased the packs should confirm the licence covers
republication before this goes any wider.
