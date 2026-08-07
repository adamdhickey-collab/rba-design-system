#!/usr/bin/env python3
"""Stage Envato Elements previews and print library.json entries for them.

    ./tools/images-fetch-envato.py <item-url-or-id> [<item-url-or-id> ...]
    ./tools/images-fetch-envato.py --cat "Data, AI & security" ABC1234 DEF5678

Give it Envato Elements item pages. For each one it reads the title, the
contributor and the preview image straight off the page, saves the preview into
assets/images/shortlist/ as envato-<id>.webp, and prints a library.json entry
ready to paste in.

WHY THIS WORKS WHEN THE ADOBE EQUIVALENT DOES NOT
-------------------------------------------------
Adobe Stock returns 403 to scripted requests and its preview URLs carry a hash
that cannot be derived, which is why the Adobe comps in this repo were saved by
hand. Envato publishes the same information in the page's Open Graph tags, and
the og:image is a complete signed URL that fetches without a session. So the
whole thing can be automated, and this script exists because it can be.

The catch is that the signature covers the resize parameters. og:image is a
1200x630 social-card crop and bending w/h/cf_fit to get 3:2 returns 403. So the
staged preview is WIDER than the card frame and will be cropped top and bottom
in the grid. That is fine for deciding whether you want the picture and wrong
for judging its composition — open the item page for that.

THE PREVIEW IS WATERMARKED. THE REAL DOWNLOAD IS NOT, AND IS LICENSED.
----------------------------------------------------------------------
This matters more than it sounds. The fifty Adobe images in this repo are comps
for work nobody has bought: they cannot ship. An Envato Elements subscription
licenses the item on download, so anything you pull from Envato with the
subscription is genuinely usable. Once you download the clean file, drop it over
the staged preview under the same name and the watermark disappears:

    assets/images/shortlist/envato-<id>.webp

No library edit, no re-sync — the entry already points at that filename.
"""

import argparse
import html
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(ROOT, 'assets', 'images', 'shortlist')

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0 Safari/537.36')

# Item ids are the trailing token of the slug: uppercase alphanumerics. Envato
# resolves on the id alone and ignores the descriptive part, which is why a
# mistyped slug still loads — a different picture, silently. Pull the id out and
# rebuild the URL from it rather than trusting what was pasted in.
ID = re.compile(r'([A-Z0-9]{6,10})/?$')


def get(url, binary=False):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = r.read()
    return data if binary else data.decode('utf-8', 'replace')


def meta(doc, prop):
    m = re.search(r'<meta[^>]+property=["\']%s["\'][^>]+content=["\']([^"\']+)' % prop, doc)
    if not m:
        m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']%s["\']' % prop, doc)
    return html.unescape(m.group(1)) if m else None


def scrape(item):
    m = ID.search(item.strip().rstrip('/'))
    if not m:
        raise ValueError('cannot find an Envato item id in %r' % item)
    ident = m.group(1)
    url = 'https://elements.envato.com/item-%s' % ident if '/' not in item else item
    doc = get(url)

    img = meta(doc, 'og:image')
    if not img:
        raise ValueError('%s: no og:image — is that an item page?' % ident)

    title = meta(doc, 'og:title') or ''
    # "Foo Bar Stock Photo, ft. x & y - Envato" → "Foo Bar"
    title = re.split(r'\s+Stock Photo|\s+-\s+Envato', title)[0].strip()

    # The contributor is a /user/<handle> link. There are several on the page and
    # the first ones are Envato's own, so skip that handle rather than taking
    # whichever matched first — an earlier version of this did, and quietly
    # credited every photograph to "Envato".
    by = 'Envato Elements'
    for handle in re.findall(r'/user/([A-Za-z0-9_-]+)', doc):
        if handle.lower() != 'envato':
            by = handle
            break

    return {'id': ident, 'url': url, 'title': title, 'by': by, 'preview': img}


def stage(info):
    raw = get(info['preview'], binary=True)
    out = os.path.join(SHOTS, 'envato-%s.webp' % info['id'])
    try:
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(raw)).convert('RGB')
        im.save(out, 'WEBP', quality=82, method=6)
        dim = '%d x %d' % im.size
    except ImportError:
        # No Pillow: keep the bytes as they came, and say so in the filename so
        # the library entry matches what is actually on disk.
        out = out[:-5] + '.jpg'
        with open(out, 'wb') as fh:
            fh.write(raw)
        dim = 'unknown'
    return os.path.basename(out), dim, len(raw)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('items', nargs='+', help='Envato Elements item URLs or ids')
    ap.add_argument('--cat', default='TODO category',
                    help='category to put these in, e.g. "Data, AI & security"')
    args = ap.parse_args()

    os.makedirs(SHOTS, exist_ok=True)
    entries, failed = [], 0
    for it in args.items:
        try:
            info = scrape(it)
            fname, dim, nbytes = stage(info)
        except Exception as exc:                      # noqa: BLE001 — report and carry on
            print('failed %s: %s' % (it, exc), file=sys.stderr)
            failed += 1
            continue
        print('staged %-28s %-9s %5d KB  %s' % (fname, dim, nbytes // 1024, info['title'][:44]))
        entries.append({
            'source': 'envato', 'id': info['id'], 'file': fname,
            'cat': args.cat, 'title': info['title'], 'by': info['by'],
            'dim': dim + ' (watermarked preview; download the full size)',
            'why': 'TODO why this one',
            'use': 'TODO where it is for',
            'crop': 'Preview is a 1200x630 social crop, not the real aspect. '
                    'Check composition on the item page.',
            'url': info['url'],
        })

    if entries:
        print('\nPaste into the "items" array in assets/images/library.json, then '
              'run ./tools/images-sync.py:\n')
        for e in entries:
            print('    ' + json.dumps(e, ensure_ascii=False) + ',')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
