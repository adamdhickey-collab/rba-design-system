#!/usr/bin/env python3
"""Regenerate the brand-image shortlist manifest in images.html from the workbook.

    ./tools/images-sync.py
    ./tools/images-sync.py --check     # report drift, write nothing, exit 1 if stale

Source of truth is assets/images/RBA_Adobe_Stock_Shortlist.xlsx — the "All 50
Images" sheet. Edit the workbook and re-run; do not hand-edit the manifest.

WHY THE PAGE HAS NO THUMBNAILS YET
----------------------------------
The workbook is a BUYING shortlist, not an asset library. It carries titles,
contributors, dimensions, reasoning and Adobe Stock URLs — and no images. Nothing
on it is licensed yet; every row's own "AI disclosure check" column says to
confirm before licensing.

Fetching the previews is not a way round that. Adobe Stock returns 403 to
automated requests, and the previews are watermarked comps for unlicensed work,
which is not something to hotlink onto a published site.

So each card renders a labelled slot at the right size and aspect, and the page
looks for a real file at:

    assets/images/shortlist/<adobe-id>.jpg      (also .jpeg, .png, .webp)

Drop a licensed image in under its Adobe ID and the card picks it up on the next
load. No manifest edit, no rebuild, no code change — which is the whole point of
keying on the ID rather than a hand-written filename.
"""

import argparse
import json
import os
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK = os.path.join(ROOT, 'assets', 'images', 'RBA_Adobe_Stock_Shortlist.xlsx')
PAGE = os.path.join(ROOT, 'images.html')
SHOTS = os.path.join(ROOT, 'assets', 'images', 'shortlist')
PREVIEWS = os.path.join(ROOT, 'assets', 'images', 'previews.json')
BEGIN = '  <script type="application/json" id="image-manifest">'
END = '  </script>'
NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'

# Long category names from the workbook -> the short label a filter chip can wear.
SHORT = {
    'Authentic Consulting & Collaboration': 'Collaboration',
    'Digital Experience, UX & Product Design': 'Digital experience',
    'Software Engineering & Cloud Infrastructure': 'Engineering & cloud',
    'Data, AI & Cybersecurity': 'Data, AI & security',
    'Industry Transformation in Context': 'Industry context',
}


def cell(c):
    if c.get('t') == 'inlineStr':
        return ''.join(x.text or '' for x in c.iter(NS + 't'))
    v = c.find(NS + 'v')
    return (v.text or '').strip() if v is not None else ''


def read_rows():
    if not os.path.exists(BOOK):
        sys.exit('error: no workbook at %s' % os.path.relpath(BOOK, ROOT))
    z = zipfile.ZipFile(BOOK)
    # The workbook's per-category sheets are views of the same data; "All 50
    # Images" is the one that carries every column, so it is the only one read.
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    rmap = {r.get('Id'): r.get('Target') for r in rels}
    RID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
    target = None
    for s in wb.iter(NS + 'sheet'):
        if s.get('name') == 'All 50 Images':
            target = rmap[s.get(RID)]
    if not target:
        sys.exit('error: the workbook has no "All 50 Images" sheet')
    sh = ET.fromstring(z.read('xl/' + target.lstrip('/').replace('xl/', '')))
    return [[cell(c) for c in r.findall(NS + 'c')] for r in sh.iter(NS + 'row')]


def load_previews():
    """{adobe-id: url}, written by tools/images-fetch-previews.py.

    Kept in its own file rather than in the workbook because it is fetched data,
    not editorial: regenerating it should never risk clobbering someone's typing.
    A hand-entered "Preview URL" column in the workbook still wins over it."""
    if not os.path.exists(PREVIEWS):
        return {}
    try:
        return json.load(open(PREVIEWS, encoding='utf-8'))
    except ValueError:
        sys.exit('error: %s is not valid JSON' % os.path.relpath(PREVIEWS, ROOT))


def build():
    rows = read_rows()
    fetched = load_previews()
    head = rows[0]
    idx = {name: i for i, name in enumerate(head)}
    need = ['Category', 'Rank', 'Priority', 'Adobe Stock ID', 'Asset title', 'Contributor',
            'Dimensions', 'Why it stands out', 'Suggested RBA use', 'Crop / overlay note',
            'Adobe Stock URL']
    # Preview URLs are optional and come from either of two places, in order:
    # a hand-typed "Preview URL" column in the workbook, then whatever
    # tools/images-fetch-previews.py put in assets/images/previews.json. Typing
    # beats fetching so a re-fetch never overwrites a deliberate choice.
    missing = [n for n in need if n not in idx]
    if missing:
        sys.exit('error: workbook is missing column(s): %s' % ', '.join(missing))

    items, problems = [], []
    for n, r in enumerate(rows[1:], start=2):
        get = lambda k: (r[idx[k]] if idx[k] < len(r) else '').strip()
        aid = get('Adobe Stock ID')
        if not re.fullmatch(r'\d+', aid):
            problems.append('row %d: "%s" is not an Adobe Stock ID' % (n, aid))
            continue
        cat = get('Category')
        if cat not in SHORT:
            problems.append('row %d: category "%s" is not in the SHORT table in this script' % (n, cat))
            continue
        item = {
            'id': aid,
            'title': get('Asset title'),
            'cat': SHORT[cat],
            'rank': int(get('Rank') or 0),
            'priority': get('Priority'),
            'by': get('Contributor'),
            'dim': get('Dimensions'),
            'why': get('Why it stands out'),
            'use': get('Suggested RBA use'),
            'crop': get('Crop / overlay note'),
            'url': get('Adobe Stock URL'),
        }
        preview = (r[idx['Preview URL']].strip() if 'Preview URL' in idx and idx['Preview URL'] < len(r) else '')
        preview = preview or fetched.get(aid, '')
        if preview:
            item['preview'] = preview
        items.append(item)
    if problems:
        sys.exit('error: workbook has problems:\n  - ' + '\n  - '.join(problems))

    order = list(SHORT.values())
    items.sort(key=lambda i: (order.index(i['cat']), i['rank']))
    return items, order


def render(items, order):
    lines = ['  {', '    "version": "1.0",',
             '    "source": "assets/images/RBA_Adobe_Stock_Shortlist.xlsx",',
             '    "licensed": false,',
             '    "total": %d,' % len(items),
             '    "categories": %s,' % json.dumps(order, ensure_ascii=False),
             '    "items": [']
    for n, it in enumerate(items):
        lines.append('      ' + json.dumps(it, ensure_ascii=False) +
                     ('' if n == len(items) - 1 else ','))
    lines += ['    ]', '  }']
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()

    items, order = build()
    block = render(items, order)
    text = open(PAGE, encoding='utf-8').read()
    i = text.find(BEGIN)
    j = text.find(END, i + len(BEGIN)) if i >= 0 else -1
    if i < 0 or j < 0:
        sys.exit('error: could not find the manifest block in images.html')
    updated = text[:i + len(BEGIN)] + '\n' + block + '\n' + text[j:]

    staged = 0
    if os.path.isdir(SHOTS):
        have = {os.path.splitext(f)[0] for f in os.listdir(SHOTS) if not f.startswith('.')}
        staged = len([it for it in items if it['id'] in have])
    previews = len([it for it in items if it.get('preview')])

    if args.check:
        print('%d candidates in %d categories, %d staged locally, %d with a preview URL'
              % (len(items), len(order), staged, previews))
        if updated != text:
            print('manifest in images.html is STALE — run ./tools/images-sync.py')
            sys.exit(1)
        print('manifest is current')
        return

    if updated != text:
        open(PAGE, 'w', encoding='utf-8').write(updated)
    print('%d candidates across %d categories' % (len(items), len(order)))
    for c in order:
        print('  %-22s %d' % (c, sum(1 for i in items if i['cat'] == c)))
    print('\nimages staged in assets/images/shortlist/: %d of %d' % (staged, len(items)))
    print('rows carrying a Preview URL: %d of %d' % (previews, len(items)))
    if staged < len(items):
        print('Drop licensed files there named <adobe-id>.jpg to fill the remaining slots.')


if __name__ == '__main__':
    main()
