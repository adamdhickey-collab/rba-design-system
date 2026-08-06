# Brand images

**A shortlist, not an asset library.** Fifty Adobe Stock candidates, ranked within
five categories. **Nothing here is licensed.** The page exists so the shortlist can
be reviewed and decided on, not so images can be downloaded from it.

```
assets/images/
├── RBA_Adobe_Stock_Shortlist.xlsx   ← source of truth
└── shortlist/                        ← licensed files go here, named by Adobe ID
```

## Why there are no thumbnails

The workbook carries titles, contributors, dimensions, reasoning and Adobe Stock
URLs. It carries no images, and there is no honest way to add them yet:

- **Nothing is licensed.** The only previews that exist are watermarked comps for
  work RBA has not bought.
- **Adobe Stock blocks fetching them.** Automated requests to the asset pages
  return `403`, so the previews cannot be pulled programmatically even setting the
  licensing question aside.

So each card renders a labelled slot at the right size and links out to Adobe
Stock, which is the one place the actual image can be seen today.

## Filling a card in

Licence the image, then drop the file here named after its Adobe Stock ID:

```
assets/images/shortlist/1904000970.jpg
```

`.jpg`, `.jpeg`, `.png` and `.webp` all work — the page tries each in turn. The
card picks it up on the next load. **No manifest edit, no rebuild, no code
change**, which is the whole reason cards key on the Adobe ID rather than on a
filename someone has to keep in step.

Frames are 3:2, which is what most of the shortlist is shot at, so a real file
drops in without the layout shifting under it.

## Changing the shortlist

Edit the workbook — the **All 50 Images** sheet — then regenerate:

```bash
./tools/images-sync.py
```

It rewrites the manifest at the bottom of `images.html`; don't hand-edit that
block. A new category needs a line in the `SHORT` table in the script, which fails
on an unknown one rather than filing it under nothing.

```bash
./tools/images-sync.py --check    # report drift, write nothing
```

## Before anything is bought

Every row needs its **AI disclosure confirmed**. The review found no explicit
disclosure on any asset page, which is not the same as confirming there is none —
and the brief excludes AI-generated imagery, so this is the check that decides
whether a pick is valid at all.

Also per asset: the licence tier (several picks are Stocksy or other
premium-collection assets a standard subscription does not cover), the model
release against the intended use, and — for anything carrying the brand — whether
a standard-collection image is too widely licensed to be sensible.

## There is no bundle

`tools/build-bundles.sh` has no images entry. A zip of unlicensed comps would be
worse than no zip. Add one back when there is a licensed set worth shipping
together.

## What was here before

Six gradient SVG stand-ins wired into a generic photo gallery, both now removed —
the shortlist board replaced the gallery, and a placeholder that looks like a
finished asset is worse than an empty section.

The earlier hunt for real photography is worth not repeating. The canonical
design-system project has no photo library: its `uploads/` folder is screenshots
and documents, and its own slide templates render gradient placeholders labelled
"Photo background placeholder". The 32 photographs in OneDrive — `office/`,
`factory/`, `bio industrial/` — are all Getty stock, with `photoshop:Credit="Getty
Images"`, an `xmpRights:WebStatement` pointing at Getty's EULA and
`plus:DataMining` prohibited. This Adobe Stock shortlist is the answer to that
gap, which is why it needs licensing rather than importing.
