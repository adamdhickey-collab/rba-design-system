# Brand images

The six files here are **placeholders** — gradient tiles, not photographs.

## Adding an image

1. Drop the file in this folder. JPG or PNG for photography; WebP is fine too.
2. Add a row to the manifest at the bottom of `images.html` (`#image-manifest`).

```json
{
  "name": "Team collaboration",
  "file": "assets/images/team-collaboration.jpg",
  "category": "People",
  "alt": "Four colleagues around a whiteboard mid-discussion",
  "format": "JPG",
  "dimensions": "2400×1600",
  "size": "480 KB",
  "tags": ["team", "meeting", "whiteboard"]
}
```

`dimensions` and `size` are recorded by hand. A static page can't measure a file it
hasn't downloaded, and the whole point of showing them is to let someone decide
*before* downloading whether an image is big enough for the slide they're building.
Get them from Finder, or:

```bash
identify -format '%wx%h %b\n' team-collaboration.jpg   # ImageMagick
```

`alt` is not optional. Write what is actually in the frame, for someone who can't
see it — not the filename again.

## Sizing

Export at roughly 2× the largest place it will be used, then compress. A 6 MB hero
photo is a 6 MB download for every person who opens this page.

## Rights

Only put an image here if RBA has cleared it for use. If the licence is
project-limited or time-limited, note that in the `name` — this folder is treated
as "safe to use anywhere," so anything with strings attached needs to say so
loudly or stay out.

## After adding images

```bash
./tools/build-bundles.sh
```

## Why this folder is still placeholders

Searched, August 2026. Recording it so nobody repeats the hunt:

**The canonical design-system project has no photo library.** Its `uploads/` folder holds
screenshots, pasted conversation images, PDFs and spreadsheets — no photography. Its own
slide templates prove the point: `slides/14-photo-background.html` and
`slides/11-image-grid.html` both render gradient placeholders labelled "Photo background
placeholder" and "Photo 01/02/03". The published RBA system is in the same position this
folder is.

**There are 32 real photographs in OneDrive** — `office/` (9), `factory/` (14),
`bio industrial/` (9) — and every one is Getty stock. The embedded XMP is unambiguous:
`photoshop:Credit="Getty Images"`, a named contributor under `dc:Rights`, an
`xmpRights:WebStatement` pointing at Getty's EULA, and `plus:DataMining` set to prohibited.

They are not in this repo on purpose. This repo is **public**, and the gallery ships a
"Download all" zip — that combination is redistribution of licensed third-party stock, and
it would also make this page's own "cleared for RBA use" line false. If that changes, the
order of operations is: make the repo private (or move to the internal hub) first, confirm
the licence covers internal redistribution, then import with per-image credit.

**What would unblock this properly:** photography RBA owns outright, or stock licensed for
public redistribution. Either can be dropped straight in — the gallery, filtering,
downloads and bundle are all built and working against the stubs.
