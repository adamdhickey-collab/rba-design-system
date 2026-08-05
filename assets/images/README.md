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
