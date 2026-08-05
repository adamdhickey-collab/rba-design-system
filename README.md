# RBA Design System

Brand foundations and a downloadable asset library for RBA Consulting. Static HTML,
CSS and JavaScript — no build step, no dependencies, no package manager.

> **The assets are placeholders.** Structure, search, filtering, theming and downloads
> are all real and working. The logo, icons, images and templates are stubs, marked as
> such wherever they appear. **Replacing the placeholder logo is the first thing to do** —
> see [`assets/logos/README.md`](assets/logos/README.md).

## Pages

| Page | Contents |
|---|---|
| `index.html` | Home, plus Foundations: Colors, Typography, Logos |
| `icons.html` | Icon library — search, filter, download, copy SVG |
| `images.html` | Brand image gallery — filter, download |
| `templates.html` | Templates & decks — a plain table of files |

The sidebar, theme toggle and ⌘K search palette are byte-identical across all four.

## Running it

Open `index.html` directly for most things. Two features need a served origin:

- **Copy SVG** on the icon page fetches the file, which a `file://` page can't do. The
  buttons remove themselves rather than failing on click.
- Nothing else. Downloads, search, filtering and theming all work off disk.

To serve it:

```bash
python3 -m http.server 3477
```

## Adding an asset

Two steps, and no build:

1. Drop the file into the right folder under `assets/`.
2. Add a row to that page's manifest (icons and images) or a `<tr>` (templates).

Each folder has its own README with the exact filenames, formats and manifest shape:
[logos](assets/logos/README.md) · [icons](assets/icons/README.md) ·
[images](assets/images/README.md) · [templates](assets/templates/README.md)

Then rebuild the download bundles and commit them:

```bash
./tools/build-bundles.sh
```

## The zip bundles are pre-built

GitHub Pages can't zip a folder on request, and doing it in the browser would mean
shipping a zip library for a page that is otherwise dependency-free. So the bundles under
`downloads/` are built by `tools/build-bundles.sh` and committed.

**This makes staleness the one real failure mode of this repo.** A bundle can silently lag
the folder it represents. Two things guard against it: the script is the only way bundles
are made, and it stamps the build date into `app.js` so every "Download all" button shows
how old its bundle is. If you add an asset and don't run the script, the button hands
people the old set.

The script writes no bundle for an empty collection, which is why `templates.html`
currently shows no bundle button at all rather than a link that would 404.

## How it's put together

- **`styles.css`** — one stylesheet. Every token is in a single `:root` block at the top,
  with the dark theme as a short re-point below it rather than a second palette.
- **`app.js`** — one script, plain IIFEs, no dependencies. Hash-scrolling, scroll-spy,
  collapsible nav groups, theme toggle, off-canvas drawer with focus trap, ⌘K search,
  the manifest-driven asset grids, clipboard copy, and SVG serialisation for downloads.
- **Manifests are inlined** as `<script type="application/json">` rather than fetched, so
  the pages work opened straight off disk.

Two decisions worth knowing before you change things:

**Icons are painted with a CSS mask, not `<img>`.** An `<img>` renders the file's own
colors and can't inherit `currentColor`, so one monochrome file could never follow the
theme — dark mode would need a second copy of every icon. Masking paints the file's alpha
with the tile's color instead. Keep icon fills as `currentColor`.

**Color swatch labels sit below the color, never on it.** RBA's Action blue (`#3178BF`)
can't carry a label at 4.5:1 against either black or white — its best case is 3.91:1. Text
on the color would mean either shipping a swatch that fails AA or inflating the label to
reach the large-text threshold. The label sits on the card instead, so every swatch is
legible by construction whatever gets added to the palette.

## Palette provenance

Colors and typefaces come from the `:root` block in `RBA Redesign/brand.html`, labelled
"RBA brand palette — Design & Brand Guidelines v1.0".

**There may be a competing source.** There is also an `rba-brand-skills` repo and a
published RBA Design System with a `colors_and_type.css`. If those disagree with what's
here, pick which one wins and record the decision — a brand site with two sources of truth
has none.

## Typefaces

Montserrat and Libre Caslon Text, both from Google Fonts, loaded via a `<link>`. There are
no font files in this repo and no `@font-face` rules, so nothing here needs a licence
check before it ships.

Libre Caslon appears in exactly one place on this site: the type specimen, where it is the
subject rather than the voice. Headings, including the hero, are Montserrat — the
guidelines reserve the serif for editorial moments, and a reference page isn't one.

## Moving to the RBA hub

Choices made to keep that port cheap: no build step and no dependencies; all paths
relative; one stylesheet with every token in a single `:root` block; manifests inlined
rather than fetched; and all four pages sharing an identical sidebar, so the hub's own
chrome can replace it with one find-and-replace.
