# Brand images

**A working library, mostly not licensed yet.** Photography and backgrounds across
six categories, from any stock service. The page exists so images can be searched,
compared and decided on — not downloaded from. Envato images are licensed by the
subscription; the rest are comps until somebody buys them.

```
assets/images/
├── library.json                     ← SOURCE OF TRUTH. Hand-edit this.
├── shortlist/                       ← the image files, <source>-<id>.<ext>
└── RBA_Adobe_Stock_Shortlist.xlsx   ← the original review. No longer wired up.
```

## Adding, swapping and deleting

Everything goes through `library.json` and then one command:

```bash
./tools/images-sync.py
```

| | |
|---|---|
| **Swap** | Replace the file in `shortlist/`. Same source and id, nothing else changes. Different service, change `source`, `id`, `file` and `url`. |
| **Delete** | Remove the entry and the file. **Ranks are not stored**, so nothing renumbers — the images below simply move up. |
| **Add** | Drop `<source>-<id>.<ext>` into `shortlist/`, run `--adopt`, fill in the TODOs. |
| **Reorder** | Move the entry up or down its category in the array. Rank and priority follow. |
| **Decide** | Set `"status"` to `keep`, `cut` or `licensed`. Omit it and the image is `undecided`. |
| **Want** | Add an entry with **no `file` key** — a candidate you have shortlisted but not downloaded. |

### Decisions and wanted entries

These are two different things and the library keeps them apart on purpose.
**Status is a judgement about the picture. Staging is a fact about the filesystem.**
Conflating them would make "downloaded, looked at, rejected" impossible to say.

- `undecided` — the default, and where everything starts. No badge on the card.
- `keep` — earns its place.
- `cut` — rejected. The card leaves the grid entirely and only comes back under
  the "Cut" filter. The entry stays in this file, because *knowing something was
  considered and rejected* is what stops it being proposed again in six months.
- `licensed` — bought. Warns if nothing is staged, since a licensed image should
  have its clean file in `shortlist/`.

A **wanted** entry has no `file`. You found six things worth a look in one browsing
session and will download them later; before this the library could not express
that, so those candidates lived in somebody's notes and got lost. The card renders
a dashed frame reading *not downloaded yet* — visibly different from a named file
that will not load, which is a fault rather than a task.

The decision filter in the toolbar is the point of all this: **"Undecided (46)"**
turns the page from a gallery into a queue.

### Retiring what has been cut

```bash
./tools/images-sync.py --retire --dry-run    # list what would go
./tools/images-sync.py --retire              # delete the files
```

A library only improves if things leave it, and the first things that should leave
are unlicensed comps already ruled out — they cannot be used, they are the bulk of
what this repo publishes, and once the decision is made they are dead weight on a
public URL.

`--retire` deletes the staged file for anything marked `cut` **and keeps the
entry**, which turns the row back into a wanted entry: the reasoning survives, and
one download reverses it if the decision changes. It only touches `paid` comps —
free and subscription images are licensed, cost nothing to keep, and might be
wanted again.

```bash
./tools/images-sync.py --check    # drift, orphans, dangling entries. Writes nothing.
./tools/images-sync.py --adopt    # stub entries for files nothing claims
./tools/images-sync.py --prune    # drop entries whose file is gone
./tools/images-sync.py --review   # curation health — see below
```

## Keeping it good, not just valid

`--check` answers *will this build*. `--review` answers *is this still a good
library*, which is the question that actually decays. Nothing it reports breaks the
page; all of it makes the page worse if left alone. Run it whenever you add a batch.

It flags three things, each of which was a real fault in the original fifty:

- **Contributor concentration** — one photographer supplying a fifth of the library
  across four categories, which is how a brand library ends up looking like one
  person's portfolio.
- **One idea shot several ways** — clusters of images in the same category, by the
  same contributor, whose titles describe the same picture. It found the four
  interchangeable analytics shots that were holding ranks 1–4 of Data, AI & security,
  and several clusters the hand review missed.
- **Aspect ratios the 3:2 frame will ruin** — portrait, near-square, or panoramic.

**A perceptual hash was tried for the duplicate check and thrown out.** It scored the
two most obviously interchangeable images in the library at hamming distance 30, and
scored one of them against an unrelated factory photograph at 29 — it could not
separate them at all, because the duplication is compositional rather than
pixel-level: different crop, different colour, different lighting, same idea. The
metadata catches what the pixels cannot, because those images shared a contributor,
a category and the words *data*, *analyst* and *dashboard*. Don't add it back.

Reports are grouped into clusters rather than pairs. Four interchangeable images
generate six pairwise warnings, which reads as six problems and hides the only one
that matters — that the top of a category is one idea photographed four times.

The sync refuses to write a manifest that references a missing file, so the page
can never ship a card pointing at nothing. Half-finished edits are caught by
`--check` rather than by someone spotting a blank card later.

## Using more than one service

Every entry names a `source`, and every source is declared once at the top of
`library.json` with a display name, a tier and a licence line. Those strings are
what the card prints, so a free image and an unlicensed comp are never confused
for one another on screen. **Add a source before you add an image from it** —
`--adopt` refuses files whose service is not declared, on purpose.

What actually suits this brand:

| Service | Tier | What it is good for | The catch |
|---|---|---|---|
| **Envato Elements** | subscription | **Start here.** RBA already pays for it, and the subscription licenses on download — the only source in this table whose images can ship today. | Widely subscribed, so no exclusivity. Quality is uneven; the search results need filtering. |
| **Adobe Stock** | paid | The bulk of the current library. Also resells Stocksy, Westend61 and peopleimages. | Everything here is an **unlicensed comp**, and the standard subscription does not cover those premium collections. |
| **Stocksy United** | paid | The least stock-looking work available. Artist co-op, tight curation. | Priciest per image, smaller library. |
| **Getty / iStock** | paid | Collections Adobe does not carry; iStock Signature is the affordable end. | Easy to overpay for Getty when iStock has the same look. |
| **Offset / Cavan** | paid | Exclusive to their agency, so nobody else's site has it. | Advertising-tier pricing. |
| **Unsplash / Pexels** | free | Internal decks, wireframes, placeholders, anything low-stakes. | Zero exclusivity, and **no screening for third-party logos** — see below. |

### Envato is the one that is actually licensed

Worth stating plainly, because it inverts how this page should be read: the fifty
Adobe images are comps for work nobody has bought and **cannot be used in
anything**. Envato images are covered by the subscription the moment they are
downloaded. Given a choice between an Adobe comp and a comparable Envato image,
the Envato one is not merely cheaper — it is the only one of the two that exists
as an option.

```bash
./tools/images-fetch-envato.py --cat "Data, AI & security" 9Z4YMDX NKPJ5GC
```

That reads each item page, pulls the title, contributor and preview, stages the
preview as `envato-<id>.webp`, and prints library entries to paste in. It works
where the Adobe equivalent does not because Envato publishes a complete signed
preview URL in its Open Graph tags, while Adobe returns `403` to scripted
requests — which is why the Adobe comps had to be saved by hand.

Two things to know about the staged previews. They are **watermarked**, and they
are a **1200×630 social crop**, not the real aspect ratio — the signature covers
the resize parameters, so a 3:2 version cannot be requested. Judge the subject
from the card and the composition from the item page. When you download the clean
full-size file, save it over the same filename and both problems disappear with
no library edit.

### Adobe Stock, without an API key

Adobe returns `403` to any scripted request for an item **page** — every user
agent, every header combination, and the oembed endpoint. Its image **CDN** has no
check at all: a plain GET with no user agent and no referer returns the
watermarked comp.

So paste the image address rather than the page address. Right-click the preview
on Adobe Stock, choose **Copy image address**, and give that to the importer:

```bash
./tools/images-add.py --cat Technology --title "Two engineers at a whiteboard" \
  "https://as2.ftcdn.net/jpg/19/04/00/09/1000_F_1904000970_WvhiNxc....webp"
```

The Adobe id is inside that filename (`1000_F_<id>_<hash>`), so the entry and its
link back to Adobe are rebuilt from it. Only the title needs supplying, because
the CDN serves an image and not a page to read one off — and Adobe deliberately
puts its own logo in `og:image`, so even the page would not give you the picture.

This is how the original fifty comps were obtained; they just were not automated
at the time.

**Free is not automatically cheaper.** Five Unsplash candidates were reviewed for
the Engineering category and one was used. Of the rejects: one carried a Twitter
logo and a client's hashtag on the office signage, one was a geology CAD screen
rather than anything consulting-shaped, and two were portrait crops that will not
survive the 3:2 frame. That hit rate is the real cost of the free tiers — the
curation work that a paid library has already done for you.

**Exclusivity is the thing worth paying for.** For a page that says "this is what
RBA looks like", the failure mode is not a mediocre photo, it is the same photo on
a competitor's site. That argues for premium collections on the hero images and
free stock only where nobody is forming an impression of the brand.

## Every thumbnail is a watermarked comp

All fifty cards show a picture, and **every one of those pictures is an Adobe Stock
comp with the watermark still across it.** That is the point: a comp exists to be
reviewed, and this page is the review. It is not an image library, and nothing in
`shortlist/` may be used in anything that ships.

The files were saved by hand from Adobe Stock — the previews cannot be fetched
programmatically, because automated requests to the asset pages return `403`. They
are `.webp`, roughly 70 KB each, 3.5 MB for the set.

**Worth deciding deliberately:** the comp licence covers internal evaluation, and
this site is reachable publicly. If that matters, the fix is to keep `shortlist/`
out of the deployed build rather than to remove it here — the cards degrade to
labelled slots on their own when the files are absent.

## Replacing a comp with the real thing

Licensing an image does not require a code change. Overwrite the comp with the
clean file under exactly the same name:

```
assets/images/shortlist/adobe-1904000970.webp
```

The card picks it up on the next load and the watermark is simply gone. No
`library.json` edit, no re-sync.

Changing the **extension** does mean one edit, because `library.json` records the
real filename and the page requests that one URL — it no longer discovers its own
content by trying four extensions and taking whichever does not 404. Drop
`adobe-1904000970.jpg` in, update `file` on that entry, re-run the sync. `--check`
will tell you if you forget.

If a card ever needs re-staging from scratch, `tools/save-previews.html` lists every
candidate in shortlist order with its link, the exact filename to save as and a copy
button, and probes the folder as you go so it doubles as a progress tracker.
`tools/images-fetch-previews.py` does the same job in one pass given an Adobe Stock
API key.

Frames are 3:2, which is what most of the set is shot at. **Portrait images will be
cropped hard** — check any tall candidate in the grid before committing to it.

## Review of the original fifty

Every image was looked at, not just its title. **Nothing has been deleted** — these
are recommendations, and the cuts are a brand decision. Each one is a line in
`library.json` and a file in `shortlist/`.

### Four problems, in order of how much they matter

**1. One contributor is a fifth of the library.** Gorodenkoff supplies **10 of 50**,
spread across four of the five categories. Andrey Popov supplies another 5. Those
two hold 15 images between them. A brand library assembled from two photographers'
back catalogues will look like two photographers' back catalogues.

**2. There are two incompatible visual registers.** The Collaboration set (Stocksy)
and the best of Industry context (Westend61) are bright, naturally lit and observed.
The Gorodenkoff frames are dark, teal-graded and cinematically lit — a completely
different look, immediately recognisable as stock, and impossible to sit next to the
others on one page. Pick one register. The daylight one is closer to RBA's own site.

**3. Data, AI & security is four near-duplicates.** Ranks 1–4 are all Andrey Popov,
and 1, 2 and 4 are effectively the same photograph: a white desk, a convertible
laptop, hands only, a generic dashboard on screen. Three of the four are the
category's *primary picks*, so the strongest slots are the weakest images. Only 4
contributors cover the whole category.

**4. Digital experience is one cliché ten times.** Eight of the ten are wireframes,
sticky notes or colour swatches. Rank 1 has no face in it at all — a torso in a
white shirt pointing at printouts. It is the single most generic image in the set
and it is a primary pick.

### Per category

| Category | Verdict | Suggested action |
|---|---|---|
| **Collaboration** | Strongest set. 8 contributors, consistent daylight register, real interaction. | Keep. Ranks 1–4 are Stocksy, so confirm the budget covers them. |
| **Digital experience** | Weakest set. Wireframe cliché throughout, faceless primary pick. | Replace ranks 1, 3, 8 and 10. Show the work on screens, not on walls. |
| **Engineering & cloud** | Split. Rank 1 (Marko Geber) is excellent; 4 Gorodenkoff frames drag it dark. | Keep 1. Cut the Gorodenkoff duplicates back to one. |
| **Data, AI & security** | Broken by duplication. 4 contributors for 10 images. | Cut two of ranks 1/2/4. Rebuild from a wider pool. |
| **Industry context** | Good range, best category for real environments. | Keep. Rank 1 (Westend61) is a model for the whole library. |

### Nine picks are premium collection

Stocksy ×4, Westend61 ×2, peopleimages ×3 — **9 of 50**, including Collaboration
ranks 1–4 and Industry context rank 1. A standard Adobe subscription does not cover
these. They are also, not coincidentally, among the best images in the set, so this
is a real budget question rather than a mistake to correct.

### What was actually changed

**Four images added, nothing removed.**

- **Data, AI & security ranks 1–3**, from Envato Elements. These directly answer
  problem 3: the four Andrey Popov near-duplicates now sit at ranks 4–7 instead of
  holding the category's primary slots. All three show people reading or presenting
  data together rather than another pair of hands at a laptop, and all three are
  licensed by the subscription rather than being comps.
- **Engineering & cloud rank 2**, from Unsplash, free-licensed — real code, real
  desk, daylight, the same register as the Collaboration set, and better than the
  Gorodenkoff frames it now sits above.

Both sets of candidates were reviewed by eye, not by title. The hit rates are worth
recording, because they are the argument for paying for curation:

| Source | Reviewed | Used | Rejected for |
|---|---|---|---|
| Envato Elements | 4 | 3 | One dark boardroom shot that read as investment banking. |
| Unsplash | 5 | 1 | A Twitter logo on office signage, a geology CAD screen, two portrait crops. |

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
