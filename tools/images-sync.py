#!/usr/bin/env python3
"""Regenerate the brand-image manifest in images.html from the library.

    ./tools/images-sync.py              # validate, then write the manifest
    ./tools/images-sync.py --check      # report drift, write nothing, exit 1 if stale
    ./tools/images-sync.py --adopt      # write stub entries for unclaimed files
    ./tools/images-sync.py --prune      # drop entries whose file is missing

SOURCE OF TRUTH IS assets/images/library.json. Edit that; never hand-edit the
manifest block at the bottom of images.html, which this script owns.

WHY THIS REPLACED THE SPREADSHEET
---------------------------------
The old version read RBA_Adobe_Stock_Shortlist.xlsx. That was right when the page
was a report on one buying exercise and wrong the moment it became a library
someone maintains: adding an image meant opening Excel, deleting one meant
renumbering a rank column by hand, and the whole thing could only ever describe
Adobe Stock. The workbook stays in the folder as the record of the original
review — it is no longer wired to anything.

THREE THINGS THIS MAKES CHEAP
-----------------------------
  Swap    Replace the file in shortlist/ with a better one. If the source and id
          are unchanged, nothing else moves. If the replacement comes from a
          different service, change source, id, file and url — the four fields
          that say where a picture came from.

  Delete  Remove the entry and delete the file. Ranks are NOT stored, so nothing
          renumbers. Delete only the file and --check reports a dangling entry;
          delete only the entry and it reports an orphan file. Either way it
          tells you, which is the point.

  Add     Drop <source>-<id>.<ext> into shortlist/ and run --adopt. You get a
          stub entry with TODO markers, last in its category, ready to fill in.

RANK AND PRIORITY ARE DERIVED
-----------------------------
Rank is an item's position among the items sharing its category — move an entry
up the array to promote it. Priority follows from rank via priority_bands in
library.json (top 3 primary, next 3 strong alternative, rest supporting) unless
the entry sets priority itself. Both used to be stored per row, which meant
deleting the 4th of ten images left a gap and made nine other rows wrong.
"""

import argparse
import collections
import datetime
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, 'assets', 'images', 'library.json')
SHOTS = os.path.join(ROOT, 'assets', 'images', 'shortlist')
PAGE = os.path.join(ROOT, 'images.html')

BEGIN = '  <script type="application/json" id="image-manifest">'
END = '</script>'

EXTS = ('.webp', '.jpg', '.jpeg', '.png')
# <source>-<id>.<ext>. Split on the FIRST hyphen only: Unsplash ids are slugs and
# contain hyphens of their own.
FILENAME = re.compile(r'^([a-z0-9]+)-(.+)\.(webp|jpg|jpeg|png)$', re.I)

# "file" is NOT required. An entry without one is a WANTED image: a candidate you
# have decided is worth looking at but have not downloaded. That is a real state in
# this workflow — you find six things in a browsing session and stage them later —
# and before this the library could not express it, so those candidates lived in
# somebody's notes and got lost.
REQUIRED = ('source', 'id', 'title', 'cat', 'url')

# The decision, kept separate from whether the file happens to be on disk. Staging
# is a fact about the filesystem; status is a judgement about the picture, and
# conflating them would mean you could not say "downloaded, looked at, rejected".
STATUSES = ('undecided', 'keep', 'cut', 'licensed')
DEFAULT_STATUS = 'undecided'

STUB = {'title': 'TODO title', 'by': 'TODO contributor', 'dim': '',
        'why': 'TODO why this one', 'use': 'TODO where it is for', 'crop': '',
        'url': 'TODO link to the asset page'}


def load():
    with open(LIB, encoding='utf-8') as fh:
        return json.load(fh)


def save(lib):
    with open(LIB, 'w', encoding='utf-8') as fh:
        json.dump(lib, fh, indent=2, ensure_ascii=False)
        fh.write('\n')


def staged():
    if not os.path.isdir(SHOTS):
        return {}
    return {n: os.path.join(SHOTS, n) for n in sorted(os.listdir(SHOTS))
            if n.lower().endswith(EXTS) and not n.startswith('.')}


def priority_for(rank, bands):
    for upto, label in bands:
        if upto is None or rank <= upto:
            return label
    return bands[-1][1] if bands else ''


def validate(lib, files):
    errs, warns = [], []
    sources = lib.get('sources', {})
    cats = lib.get('categories', [])
    seen = set()

    for n, it in enumerate(lib.get('items', []), 1):
        where = 'item %d (%s)' % (n, it.get('file') or it.get('id') or '?')
        for f in REQUIRED:
            if not it.get(f):
                errs.append('%s: missing "%s"' % (where, f))
        if it.get('source') and it['source'] not in sources:
            errs.append('%s: unknown source "%s" — add it to "sources" first'
                        % (where, it['source']))
        if it.get('cat') and it['cat'] not in cats:
            errs.append('%s: category "%s" is not in "categories"' % (where, it['cat']))

        key = (it.get('source'), it.get('id'))
        if key in seen:
            errs.append('%s: duplicate %s/%s' % (where, key[0], key[1]))
        seen.add(key)

        st = it.get('status', DEFAULT_STATUS)
        if st not in STATUSES:
            errs.append('%s: status "%s" is not one of %s'
                        % (where, st, ', '.join(STATUSES)))
        if st == 'licensed' and not it.get('file'):
            warns.append('%s: marked licensed but nothing is staged — the licensed '
                         'file should be in shortlist/' % where)

        f = it.get('file')
        # A missing "file" key means wanted-but-not-downloaded, which is fine. A
        # "file" that names something not on disk is a broken entry, which is not.
        if f and f not in files:
            errs.append('%s: names %s but there is no such file in shortlist/. '
                        'Delete the "file" key to make it a wanted entry, or --prune it.'
                        % (where, f))
        if f:
            m = FILENAME.match(f)
            if not m:
                warns.append('%s: filename is not <source>-<id>.<ext>' % where)
            elif (m.group(1).lower() != str(it.get('source', '')).lower()
                  or m.group(2) != str(it.get('id'))):
                # Only a convention, but a file named adobe-123 under an unsplash
                # entry is exactly the sort of thing nobody spots until the
                # outbound link sends someone to the wrong picture.
                warns.append('%s: filename says %s/%s, entry says %s/%s'
                             % (where, m.group(1), m.group(2), it.get('source'), it.get('id')))

    claimed = {it.get('file') for it in lib.get('items', [])}
    for f in sorted(set(files) - claimed):
        warns.append('orphan file: shortlist/%s is claimed by no entry '
                     '— run --adopt, or delete it' % f)
    return errs, warns


def build(lib):
    bands = [(None if u is None else int(u), l) for u, l in lib.get('priority_bands', [])]
    cats = lib['categories']
    per = {c: 0 for c in cats}
    items = []
    for it in sorted(lib['items'], key=lambda x: cats.index(x['cat'])):
        per[it['cat']] += 1
        rank = per[it['cat']]
        src = lib['sources'][it['source']]
        items.append({
            'id': it['id'],
            'source': it['source'],
            'sourceName': src['name'],
            'licence': src.get('licence', ''),
            'tier': src.get('tier', ''),
            'file': it.get('file', ''),
            'status': it.get('status', DEFAULT_STATUS),
            'title': it['title'],
            'cat': it['cat'],
            'rank': rank,
            'priority': it.get('priority') or priority_for(rank, bands),
            'by': it.get('by', ''),
            'dim': it.get('dim', ''),
            'why': it.get('why', ''),
            'use': it.get('use', ''),
            'crop': it.get('crop', ''),
            'url': it['url'],
        })
    return {
        'version': 2,
        'generated': datetime.date.today().isoformat(),
        'total': len(items),
        'sources': lib['sources'],
        'categories': cats,
        'items': items,
    }


def render(m):
    lines = ['    {',
             '      "version": %d,' % m['version'],
             '      "generated": "%s",' % m['generated'],
             '      "total": %d,' % m['total'],
             '      "sources": %s,' % json.dumps(m['sources'], ensure_ascii=False),
             '      "categories": %s,' % json.dumps(m['categories'], ensure_ascii=False),
             '      "items": [']
    lines.append(',\n'.join('        ' + json.dumps(i, ensure_ascii=False) for i in m['items']))
    lines += ['      ]', '    }']
    return '\n'.join(lines)


def adopt(lib, files):
    claimed = {it.get('file') for it in lib['items']}
    added = []
    for f in sorted(set(files) - claimed):
        m = FILENAME.match(f)
        if not m:
            print('  skipped %s — not <source>-<id>.<ext>, so there is no way to '
                  'tell which service it came from' % f)
            continue
        source, ident = m.group(1).lower(), m.group(2)
        if source not in lib['sources']:
            print('  skipped %s — source "%s" is not in library.json "sources"' % (f, source))
            continue
        entry = {'source': source, 'id': ident, 'file': f, 'cat': lib['categories'][0]}
        entry.update(STUB)
        lib['items'].append(entry)
        added.append(f)
        print('  adopted %s → "%s", fill in the TODOs' % (f, entry['cat']))
    return added


def prune(lib, files):
    """Drop entries that NAME a file which is not there.

    Deliberately leaves wanted entries (no "file" key at all) alone. Before status
    and wanted existed this dropped anything without a staged file, which would now
    delete every candidate you had shortlisted but not yet downloaded — the exact
    thing the wanted state was added to keep.
    """
    keep, gone = [], []
    for it in lib['items']:
        if not it.get('file') or it['file'] in files:
            keep.append(it)
        else:
            gone.append(it['file'])
            print('  pruned %s — named a file that is not in shortlist/' % it['file'])
    lib['items'] = keep
    return gone


# Words that appear in nearly every title here and so carry no signal about
# whether two pictures are the same picture.
STOP = set('a an and at by for from in of on the to with using use working work '
           'business office modern people person team man woman young'.split())


def title_overlap(a, b):
    """How much two titles say the same thing, 0 to 1."""
    wa = {w for w in re.findall(r'[a-z]+', a.lower()) if w not in STOP and len(w) > 2}
    wb = {w for w in re.findall(r'[a-z]+', b.lower()) if w not in STOP and len(w) > 2}
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / min(len(wa), len(wb))


# A perceptual hash was tried here first and thrown away, which is worth recording
# so nobody adds it back. dHash scored the two images in this library that are most
# obviously the same shot — a white desk, a laptop, hands, a dashboard — at hamming
# distance 30, and scored one of them against an unrelated factory photograph at 29.
# It could not separate them, because the duplication is compositional rather than
# pixel-level: different crop, different colour, different lighting, same idea.
#
# The metadata catches what the pixels cannot. Those four images shared a
# contributor, a category, and the words "data", "analyst" and "dashboard". That is
# the signal.


def aspect(path):
    try:
        from PIL import Image
        with Image.open(path) as im:
            return im.size[0] / im.size[1]
    except Exception:                                  # noqa: BLE001
        return None


def review(lib, files):
    """The health of the library as a set, not the validity of its entries.

    validate() answers "will this build?". This answers "is this a good library?",
    which is the question that actually decays over time — nothing here breaks the
    page, and all of it makes the page worse if left alone.
    """
    items = lib['items']
    n = len(items)
    notes = []

    # Contributor concentration. The original fifty had one photographer supplying
    # ten of them across four categories, which is how a brand library ends up
    # looking like one person's portfolio.
    by = collections.Counter(i.get('by', '') for i in items if i.get('by'))
    for name, count in by.most_common():
        if count >= max(4, n * 0.08):
            cats = sorted({i['cat'] for i in items if i.get('by') == name})
            notes.append('%s supplies %d of %d images (%.0f%%), across %d categor%s'
                         % (name, count, n, 100.0 * count / n, len(cats),
                            'y' if len(cats) == 1 else 'ies'))

    # Per-category contributor spread.
    for cat in lib['categories']:
        rows = [i for i in items if i['cat'] == cat]
        if len(rows) < 4:
            continue
        spread = collections.Counter(i.get('by', '') for i in rows)
        top, count = spread.most_common(1)[0]
        if count >= max(3, len(rows) * 0.35):
            notes.append('"%s": %d of %d from %s' % (cat, count, len(rows), top or 'one contributor'))
        if len(spread) <= len(rows) / 2.5:
            notes.append('"%s": only %d contributors for %d images'
                         % (cat, len(spread), len(rows)))

    # Probable near-duplicates: same category, same contributor, and titles that
    # describe the same thing. Any one of those alone is fine; all three together
    # is how the same photograph ends up in the shortlist twice.
    # Reported as CLUSTERS, not pairs. Four interchangeable images produce six
    # pairwise warnings, which reads as six problems and buries the one that
    # matters — that the top of a category is one idea photographed four times.
    for cat in lib['categories']:
        rows = [i for i in items if i['cat'] == cat]
        parent = list(range(len(rows)))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for a in range(len(rows)):
            for b in range(a + 1, len(rows)):
                ia, ib = rows[a], rows[b]
                same_by = ia.get('by') and ia.get('by') == ib.get('by')
                overlap = title_overlap(ia.get('title', ''), ib.get('title', ''))
                if (same_by and overlap >= 0.4) or overlap >= 0.7:
                    parent[find(a)] = find(b)

        groups = collections.defaultdict(list)
        for n in range(len(rows)):
            groups[find(n)].append(n)
        for members in groups.values():
            if len(members) < 2:
                continue
            ranks = ', '.join(str(n + 1) for n in members)
            who = {rows[n].get('by') for n in members}
            notes.append('"%s" ranks %s look like one idea shot %d ways%s — %s'
                         % (cat, ranks, len(members),
                            ' (all by %s)' % who.pop() if len(who) == 1 else '',
                            ', '.join(rows[n]['file'] for n in members)))

    # Portrait and near-square images that the 3:2 frame will crop hard.
    checked = False
    for it in items:
        p = files.get(it.get('file'))
        if not p:
            continue
        a = aspect(p)
        if a is None:
            continue
        checked = True
        # 3:2 is 1.50 and the frame is forgiving either side of it. 16:9 (1.78) is
        # what most stock is shot at and crops fine, so flagging it made twenty
        # warnings about nothing and hid the two that mattered. Only call out
        # ratios that lose real subject matter.
        if a < 1.15:
            notes.append('%s is %s (%.2f:1) — the card frame is 3:2 and will crop it hard'
                         % (it['file'], 'portrait' if a < 1 else 'nearly square', a))
        elif a > 2.2:
            notes.append('%s is panoramic (%.2f:1) — 3:2 will cut a third off the '
                         'top and bottom' % (it['file'], a))
    if items and not checked:
        notes.append('(install Pillow to check aspect ratios)')
    return notes


def retire(lib, files, apply_it):
    """Delete the staged file for anything cut, keeping the entry as the record.

    The library only improves if things leave it, and the ones that should leave
    first are unlicensed comps that have already been ruled out — they cannot be
    used, they are the bulk of what this repo publishes, and once a decision is
    made they are dead weight sitting on a public URL.

    The ENTRY survives, with its reasoning intact. Knowing that a picture was
    considered and rejected is worth as much as the shortlist itself; it is what
    stops the same image being proposed again in six months. What goes is the file,
    which turns the row back into a wanted entry — recoverable in one download if
    the decision is ever reversed.

    Only comps are retired. A 'free' or 'subscription' image is licensed, costs
    nothing to keep, and might be wanted again.
    """
    done = []
    for it in lib['items']:
        if it.get('status') != 'cut' or not it.get('file'):
            continue
        tier = lib['sources'].get(it['source'], {}).get('tier')
        if tier != 'paid':
            print('  kept %s — %s is %s, not an unlicensed comp'
                  % (it['file'], it['source'], tier or 'untiered'))
            continue
        path = files.get(it['file'])
        print('  %s %s (%s)' % ('retiring' if apply_it else 'would retire',
                                it['file'], it['title'][:44]))
        if apply_it:
            if path and os.path.exists(path):
                os.remove(path)
            it.pop('file', None)
        done.append(it['id'])
    return done


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true', help='report drift, write nothing')
    ap.add_argument('--adopt', action='store_true', help='add stub entries for unclaimed files')
    ap.add_argument('--prune', action='store_true', help='drop entries whose file is gone')
    ap.add_argument('--review', action='store_true',
                    help='curation health: concentration, near-duplicates, bad aspects')
    ap.add_argument('--retire', action='store_true',
                    help='delete staged comps for anything cut; keeps the entry')
    ap.add_argument('--dry-run', action='store_true',
                    help='with --retire, list what would go and change nothing')
    args = ap.parse_args()

    lib = load()
    files = staged()

    if args.review:
        notes = review(lib, files)
        if not notes:
            print('%d images — nothing flagged.' % len(lib['items']))
            return 0
        print('Curation notes on %d images. None of these break the build; '
              'they are judgement calls.\n' % len(lib['items']))
        for note in notes:
            print('  · %s' % note)
        return 0

    if args.retire:
        print('Retiring cut comps%s:' % (' (dry run)' if args.dry_run else ''))
        gone = retire(lib, files, not args.dry_run)
        if not gone:
            print('  nothing to retire — mark something "cut" in library.json first')
        elif not args.dry_run:
            save(lib)
            files = staged()
            print('  retired %d; entries kept as wanted, files deleted\n' % len(gone))
        else:
            print('  %d would be retired. Re-run without --dry-run.\n' % len(gone))
            return 0

    if args.adopt or args.prune:
        if args.adopt:
            print('Adopting unclaimed files:')
            if not adopt(lib, files):
                print('  nothing to adopt')
        if args.prune:
            print('Pruning dangling entries:')
            if not prune(lib, files):
                print('  nothing to prune')
        save(lib)
        print('Updated %s\n' % os.path.relpath(LIB, ROOT))

    errs, warns = validate(lib, files)
    for w in warns:
        print('warning: %s' % w, file=sys.stderr)
    if errs:
        for e in errs:
            print('error: %s' % e, file=sys.stderr)
        print('\n%d error(s). Manifest not written.' % len(errs), file=sys.stderr)
        return 2

    block = render(build(lib))
    with open(PAGE, encoding='utf-8') as fh:
        text = fh.read()
    i = text.find(BEGIN)
    j = text.find(END, i + len(BEGIN)) if i >= 0 else -1
    if i < 0 or j < 0:
        print('error: could not find the manifest block in images.html', file=sys.stderr)
        return 2
    updated = text[:i + len(BEGIN)] + '\n' + block + '\n  ' + text[j:]

    # The generated stamp moves every day, so a raw comparison would report drift
    # on a file nobody touched. Compare everything except the stamp.
    strip = lambda s: re.sub(r'"generated": "[^"]*",', '', s)
    stale = strip(updated) != strip(text)

    n = len(lib['items'])
    wanted = sum(1 for it in lib['items'] if not it.get('file'))
    by_status = collections.Counter(it.get('status', DEFAULT_STATUS) for it in lib['items'])

    def summary():
        print('  staged %d, wanted %d' % (n - wanted, wanted))
        print('  ' + ', '.join('%s %d' % (s, by_status[s]) for s in STATUSES if by_status[s]))
        undecided = by_status['undecided']
        if undecided:
            print('  %d still undecided — ./tools/images-sync.py --review for '
                  'what to look at first' % undecided)

    if args.check:
        print('%d images, %d categories, %d sources — %s'
              % (n, len(lib['categories']), len(lib['sources']),
                 'manifest is STALE, run ./tools/images-sync.py' if stale
                 else 'manifest is current'))
        summary()
        return 1 if stale else 0

    with open(PAGE, 'w', encoding='utf-8') as fh:
        fh.write(updated)
    print('Wrote manifest: %d images, %d categories' % (n, len(lib['categories'])))
    for s, meta in lib['sources'].items():
        c = sum(1 for it in lib['items'] if it['source'] == s)
        print('  %-10s %2d  %s' % (s, c, meta['name']))
    summary()
    return 0


if __name__ == '__main__':
    sys.exit(main())
