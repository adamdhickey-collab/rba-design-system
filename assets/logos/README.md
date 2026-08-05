# Logos

**Everything in this folder is a placeholder.** Replacing it is the first thing to do.

## What to drop here

| Filename | What it is |
|---|---|
| `rba-logo-primary.svg` | Midnight wordmark, red monogram. The default. |
| `rba-logo-white.svg` | Fully reversed. For midnight fills, black, and photography. |
| `rba-logo-black.svg` | One-color black, for single-ink print and engraving. |
| `rba-logo-red.svg` | One-color red, where only the accent may appear. |

SVG only. Outlined paths, not live text — a wordmark that depends on a font
installed on the viewer's machine will render wrong somewhere, and probably in a
client's browser.

## Then update the page

`index.html` carries the logo once, as an inline `<symbol id="rba-logo">` near the
top of `<body>`, and every card on the Logos section references it with `<use>`.
Replace that symbol's contents with the real artwork.

Two contracts to keep, because the four colorways and the download button both
depend on them:

- **The wordmark paths must use `fill="currentColor"`** (or inherit it). `color` on
  the `<svg>` is what paints it, and that's set by the `.brand-logo--*` classes.
- **The monogram must use `style="fill: var(--mark-fill, #C8252D)"`.** Same reason:
  `--mark-fill` is what each colorway repoints.

Get those right and all four colorways work from one copy of the art, and the
download button serializes each one correctly — including baking the resolved
color in as a literal, so the downloaded file is right when opened in Preview or a
design tool rather than a browser. See the "Asset downloads" block in `app.js`.

## Finally

Delete the placeholder warning from the Logos section of `index.html`, delete
`rba-logo-placeholder.svg`, and rebuild the bundle:

```bash
./tools/build-bundles.sh
```

## Favicons and app icons

`../favicons/` holds the browser and app icons built from the block lockup —
`favicon-16.png`, `favicon-32.png`, `apple-touch-180.png`. This site uses them as its
own favicon, and they ship inside `downloads/rba-logos.zip`.

The design-system project also has `mark-on-navy-512.png`, `mark-transparent-512.png`,
`maskable-512.png` and `favicon-48.png`. Those weren't imported — pull them across if a
PWA manifest or a large app icon is ever needed.
