# Icons

The twelve SVGs here are **placeholders** — simple geometric stand-ins so the
library's search, filtering, download and copy all work before real icons arrive.

## Adding an icon

Two steps. There is no build.

1. Drop the SVG in this folder.
2. Add a row to the manifest at the bottom of `icons.html` (`#icon-manifest`).

```json
{ "name": "handshake", "file": "assets/icons/handshake.svg", "category": "Services", "tags": ["partner", "deal", "agreement"] }
```

Leave `placeholder` off entirely for a real icon. `tags` is what makes the icon
findable by someone who doesn't know our naming — a person hunting for a partner
icon may well type "deal".

## File requirements

- **24×24 viewBox.** The grid the whole set is drawn on. Off-grid icons blur.
- **`fill="currentColor"`**, single path where possible, no hard-coded hex.
- **No `<style>` blocks, no classes, no ids.** Files are inlined and copied around;
  ids collide and styles leak.
- Name the file exactly what the icon is, lowercase, hyphenated.

## Why the icons look right in dark mode

They're painted as a CSS **mask**, not an `<img>`. An `<img>` renders the file's
own colors and cannot inherit `currentColor`, so a single monochrome file could
never follow the theme — dark mode would need a second copy of every icon. The
mask paints the file's alpha channel with the tile's color instead, so one file
serves both themes and stays a normal downloadable SVG.

The practical consequence: **the fill color inside the file is ignored on this
page** but matters everywhere else the file is used. Keep it `currentColor`.

## Copy SVG needs a served page

The copy button fetches the file, which the browser blocks on a `file://` page.
The buttons remove themselves when the page isn't served over http — download
still works. Serve the folder if you need copy:

```bash
python3 -m http.server 3477
```

## After adding icons

```bash
./tools/build-bundles.sh
```

Then commit the zips and `app.js` alongside your new files.
