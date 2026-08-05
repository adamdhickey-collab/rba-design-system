#!/usr/bin/env python3
"""Stage the icon packs into assets/ and regenerate the manifest in icons.html.

    ./tools/icons-sync.py            # sync, then report what changed
    ./tools/icons-sync.py --check    # report only, touch nothing (exit 1 if stale)

WHY THIS EXISTS
---------------
The icons arrive as 80 stock packs under icons/, each one a folder holding an
Illustrator source, an EPS, a svg/ folder and a png/ folder. Only the svg/ and
png/ files belong on the site: icons/ itself is 124 MB, almost all of it .ai and
.eps that nobody downloading an icon from a web page will ever open. So icons/
is a working drop — gitignored — and this script copies the 2,980 files that are
actually served into assets/icons/, one folder per pack.

Doing it by hand is not an option at this size, and doing it by hand is also how
the manifest and the folder drift apart. This script is the only supported way
to add a pack.

FILENAMES ARE NORMALISED, AND THAT IS DELIBERATE
------------------------------------------------
Source names are inconsistent: "IT Administrator-14.svg", "online shopping-03.svg",
"building-07.svg". 332 of the 1,490 contain a space and the capitalisation is
per-pack rather than per-set. Serving those verbatim means percent-encoded URLs
and case-sensitivity bugs that only show up on Linux hosting, so on disk every
file becomes <pack-slug>-NN.svg.

The original casing is not lost — it is the pack's `name` in the manifest, which
is what the tile displays and what search matches. "IT Administrator-14" is still
what you see and still what you can type.

RENAMING LATER
--------------
The names are `Productivity-01` and so on, which tells you nothing. The plan is
to give each icon a real name so search works. That is what `labels` is for: a
per-pack map of icon number to a human name.

    "labels": { "01": "settings-gear", "04": "checklist" }

A label wins over the generated name wherever the icon appears, and it is added
to the search haystack alongside it. THIS SCRIPT PRESERVES LABELS ACROSS RUNS —
it reads the existing manifest out of icons.html before rewriting it, so naming
work is never lost to a re-sync. That is the single most important thing this
script does, and the round-trip is covered by --check.
"""

import argparse
import filecmp
import json
import os
import re
import shutil
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'icons')
DEST = os.path.join(ROOT, 'assets', 'icons')
PAGE = os.path.join(ROOT, 'icons.html')

BEGIN = '  <script type="application/json" id="icon-manifest">'
END = '  </script>'

# Groups. Eight of them, because the 80 pack names are themselves the useful
# filter and chips for 80 packs would be a wall — the packs live in a select
# instead. Every pack below belongs to exactly one group; the script fails if a
# pack on disk is missing from this table, so a new drop cannot be filed silently
# under nothing.
GROUPS = [
    'Business & strategy',
    'Data & analytics',
    'Technology',
    'Finance & sales',
    'People & teams',
    'Documents & legal',
    'Communication & marketing',
    'Operations & workplace',
]

# slug -> (display name, group, search keywords)
#
# The keywords are the reason search is usable before anything is renamed. With
# names like "Sales Report-07" the only thing worth matching is the pack, so each
# pack carries the words someone would actually type looking for it. "chart" has
# to find the analytics packs even though no file is called chart.
PACKS = {
    # ---- Business & strategy ----
    'blueprint':          ('Blueprint', 'Business & strategy', 'plan draft architecture drawing spec design document scheme'),
    'business':           ('Business', 'Business & strategy', 'company enterprise corporate commerce growth deal'),
    'business-report':    ('Business Report', 'Business & strategy', 'chart graph analysis summary results dashboard metrics kpi'),
    'choice':             ('Choice', 'Business & strategy', 'decision option select fork alternative path pick'),
    'compass':            ('Compass', 'Business & strategy', 'direction navigate orientation guidance north bearing'),
    'market-study':       ('Market Study', 'Business & strategy', 'research survey analysis segment competitor insight'),
    'mindset':            ('Mindset', 'Business & strategy', 'thinking attitude brain mindfulness psychology growth'),
    'motivation':         ('Motivation', 'Business & strategy', 'drive inspire energy goal ambition encouragement'),
    'opinion':            ('Opinion', 'Business & strategy', 'feedback review rating comment survey voice sentiment'),
    'prototype':          ('Prototype', 'Business & strategy', 'wireframe mockup mvp draft iteration concept model'),
    'route':              ('Route', 'Business & strategy', 'roadmap path journey milestone map direction step'),
    'vision':             ('Vision', 'Business & strategy', 'strategy future goal target telescope foresight ambition'),
    'wisdom':             ('Wisdom', 'Business & strategy', 'knowledge insight experience learning owl advice'),

    # ---- Data & analytics ----
    'big-data':           ('Big Data', 'Data & analytics', 'database warehouse lake pipeline volume storage server cluster'),
    'business-analytics': ('Business Analytics', 'Data & analytics', 'chart graph dashboard metrics kpi report insight bi power'),
    'neuroscience':       ('Neuroscience', 'Data & analytics', 'brain ai machine learning neural network cognition intelligence'),
    'robotics':           ('Robotics', 'Data & analytics', 'robot automation ai bot machine rpa android'),

    # ---- Technology ----
    'circuit':            ('Circuit', 'Technology', 'chip hardware board electronics processor iot embedded'),
    'front-end-developer': ('Front End Developer', 'Technology', 'code programming web html css javascript engineer build'),
    'ftp':                ('FTP', 'Technology', 'transfer upload download server file network protocol sync'),
    'it-administrator':   ('IT Administrator', 'Technology', 'sysadmin server infrastructure support network ops helpdesk'),
    'link':               ('Link', 'Technology', 'url hyperlink chain connect share reference anchor'),
    'troubleshooting':    ('Troubleshooting', 'Technology', 'debug fix repair support wrench problem error diagnose'),
    'validation':         ('Validation', 'Technology', 'check verify approve test quality confirm tick compliance'),
    'website-builder':    ('Website Builder', 'Technology', 'web page cms layout template site design browser'),

    # ---- Finance & sales ----
    'ai-finance':         ('AI Finance', 'Finance & sales', 'artificial intelligence machine learning fintech automation money'),
    'audit':              ('Audit', 'Finance & sales', 'compliance review inspection accounting check control governance'),
    'distributor':        ('Distributor', 'Finance & sales', 'supply chain wholesale channel partner logistics reseller'),
    'finance':            ('Finance', 'Finance & sales', 'money cash budget accounting bank currency dollar payment'),
    'fintech':            ('Fintech', 'Finance & sales', 'digital banking payment wallet crypto mobile money app'),
    'global-finance':     ('Global Finance', 'Finance & sales', 'international currency exchange world market forex trade'),
    'invoice':            ('Invoice', 'Finance & sales', 'bill receipt payment billing statement account due'),
    'monetization':       ('Monetization', 'Finance & sales', 'revenue income earnings profit pricing subscription monetise'),
    'online-shopping':    ('Online Shopping', 'Finance & sales', 'ecommerce cart basket retail checkout store buy commerce'),
    'sales':              ('Sales', 'Finance & sales', 'selling revenue deal pipeline target quota conversion'),
    'sales-report':       ('Sales Report', 'Finance & sales', 'chart graph revenue forecast performance dashboard metrics'),
    'savings':            ('Savings', 'Finance & sales', 'piggy bank deposit interest fund reserve nest egg'),

    # ---- People & teams ----
    'administrator':      ('Administrator', 'People & teams', 'admin manager user role permission account staff'),
    'client':             ('Client', 'People & teams', 'customer account stakeholder buyer relationship crm'),
    'collaboration':      ('Collaboration', 'People & teams', 'teamwork partnership together cooperate group handshake'),
    'community':          ('Community', 'People & teams', 'group people network social members audience together'),
    'consultant':         ('Consultant', 'People & teams', 'advisor expert specialist professional adviser engagement'),
    'customer-service':   ('Customer Service', 'People & teams', 'support helpdesk call centre agent chat assistance'),
    'expert':             ('Expert', 'People & teams', 'specialist professional skill mastery authority guru'),
    'freelancer':         ('Freelancer', 'People & teams', 'contractor remote independent gig self employed'),
    'internship':         ('Internship', 'People & teams', 'trainee junior graduate placement apprentice learning'),
    'leadership':         ('Leadership', 'People & teams', 'manager executive director boss lead vision team'),
    'mentoring':          ('Mentoring', 'People & teams', 'coaching training guidance teach develop support growth'),
    'referral':           ('Referral', 'People & teams', 'recommend refer word of mouth invite share network'),
    'teamwork':           ('Teamwork', 'People & teams', 'collaboration group together cooperate squad crew'),
    'vip':                ('VIP', 'People & teams', 'premium priority exclusive loyalty tier elite member'),
    'working-shift':      ('Working Shift', 'People & teams', 'roster schedule hours rota time clock attendance'),

    # ---- Documents & legal ----
    'catalog':            ('Catalog', 'Documents & legal', 'catalogue brochure listing product index directory'),
    'certificate':        ('Certificate', 'Documents & legal', 'award diploma accreditation badge qualification credential'),
    'copyright':          ('Copyright', 'Documents & legal', 'ip intellectual property trademark licence legal rights'),
    'employment-contract': ('Employment Contract', 'Documents & legal', 'hr agreement offer hire signature terms job'),
    'journal':            ('Journal', 'Documents & legal', 'notebook diary log record publication write'),
    'legal-document':     ('Legal Document', 'Documents & legal', 'law contract agreement court compliance policy terms'),
    'license':            ('License', 'Documents & legal', 'licence permit certificate authorisation entitlement key'),
    'office-document':    ('Office Document', 'Documents & legal', 'file paper word docx folder archive record'),
    'paperwork':          ('Paperwork', 'Documents & legal', 'forms admin filing documents bureaucracy record'),

    # ---- Communication & marketing ----
    'breaking-news':      ('Breaking News', 'Communication & marketing', 'alert headline urgent bulletin press media announcement'),
    'communication':      ('Communication', 'Communication & marketing', 'message chat email call talk conversation contact'),
    'creative-skills':    ('Creative Skills', 'Communication & marketing', 'design art idea craft illustration creativity make'),
    'design-agency':      ('Design Agency', 'Communication & marketing', 'studio branding creative art direction ux ui portfolio'),
    'flyer':              ('Flyer', 'Communication & marketing', 'leaflet poster print handout promotion advert'),
    'news':               ('News', 'Communication & marketing', 'press media article newspaper journalism headline'),
    'newsletter':         ('Newsletter', 'Communication & marketing', 'email campaign subscribe mailing list broadcast'),
    'presentation':       ('Presentation', 'Communication & marketing', 'slides deck powerpoint pitch talk projector meeting'),
    'selfie':             ('Selfie', 'Communication & marketing', 'photo camera phone portrait social picture'),
    'webinar':            ('Webinar', 'Communication & marketing', 'online seminar broadcast stream video conference training'),
    'workshop':           ('Workshop', 'Communication & marketing', 'training session facilitation whiteboard collaborate learn'),

    # ---- Operations & workplace ----
    'building':           ('Building', 'Operations & workplace', 'office tower property real estate architecture city'),
    'delivery':           ('Delivery', 'Operations & workplace', 'shipping logistics parcel courier truck package transport'),
    'landscape':          ('Landscape', 'Operations & workplace', 'nature scenery outdoor environment mountain view'),
    'office':             ('Office', 'Operations & workplace', 'workplace desk workspace room corporate facility'),
    'productivity':       ('Productivity', 'Operations & workplace', 'efficiency workflow task time management focus output'),
    'schedule':           ('Schedule', 'Operations & workplace', 'calendar diary planner appointment date timeline booking'),
    'warehouse':          ('Warehouse', 'Operations & workplace', 'storage inventory stock logistics depot fulfilment'),
    'workflow':           ('Workflow', 'Operations & workplace', 'process automation pipeline steps flowchart sequence'),
}

# The date stamp and the -outline-icons- infix are drop artefacts, not identity.
PACK_DIR_RE = re.compile(r'^(?P<slug>.+?)-outline-iconss?-\d{4}-\d{2}-\d{2}(?:-\d{2}){3}-utc$')
STEM_RE = re.compile(r'^(?P<prefix>.*?)-(?P<num>\d+)$')


def die(msg):
    print('error: ' + msg, file=sys.stderr)
    sys.exit(1)


def scan_source():
    """Read icons/ into [(slug, [numbers]), ...], failing loudly on anything odd."""
    if not os.path.isdir(SRC):
        die('no source drop at %s. This script syncs FROM icons/ INTO assets/icons/;\n'
            '       without it there is nothing to sync. Use --check to verify what is\n'
            '       already staged.' % os.path.relpath(SRC, ROOT))

    packs, problems = [], []
    for entry in sorted(os.listdir(SRC)):
        path = os.path.join(SRC, entry)
        if not os.path.isdir(path):
            continue
        m = PACK_DIR_RE.match(entry)
        if not m:
            problems.append('%s: folder name does not look like a pack drop' % entry)
            continue
        slug = m.group('slug')

        svg_dir, png_dir = os.path.join(path, 'svg'), os.path.join(path, 'png')
        if not os.path.isdir(svg_dir):
            problems.append('%s: no svg/ folder' % entry)
            continue

        nums = []
        for f in sorted(os.listdir(svg_dir)):
            if not f.lower().endswith('.svg'):
                continue
            sm = STEM_RE.match(f[:-4])
            if not sm:
                problems.append('%s/svg/%s: expected <Name>-NN.svg' % (entry, f))
                continue
            # A PNG is not optional. Every tile offers both formats, so a missing
            # one would ship a download button pointing at a 404.
            if not os.path.exists(os.path.join(png_dir, f[:-4] + '.png')):
                problems.append('%s/svg/%s: no matching PNG' % (entry, f))
                continue
            nums.append((sm.group('num'), os.path.join(svg_dir, f),
                         os.path.join(png_dir, f[:-4] + '.png')))

        if not nums:
            problems.append('%s: no usable icons' % entry)
            continue
        if slug not in PACKS:
            problems.append('%s: pack "%s" is not in the PACKS table in this script.\n'
                            '         Add it with a display name, one of the eight groups, '
                            'and search keywords.' % (entry, slug))
            continue
        packs.append((slug, sorted(nums, key=lambda t: t[0])))

    if problems:
        die('the source drop has problems:\n       - ' + '\n       - '.join(problems))
    return packs


def read_existing_manifest():
    """Pull the current manifest out of icons.html so labels survive a re-sync."""
    if not os.path.exists(PAGE):
        return {}
    text = open(PAGE, encoding='utf-8').read()
    i = text.find(BEGIN)
    if i < 0:
        return {}
    j = text.find(END, i + len(BEGIN))
    if j < 0:
        return {}
    try:
        data = json.loads(text[i + len(BEGIN):j])
    except ValueError:
        # A hand-edit that broke the JSON must not silently discard labels.
        die('the manifest block in icons.html is not valid JSON. Fix it before\n'
            '       syncing, or the labels in it will be lost.')
    return {p['slug']: p.get('labels') or {} for p in data.get('packs', [])}


def copy_if_changed(src, dst, stats):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst) and filecmp.cmp(src, dst, shallow=False):
        stats['same'] += 1
        return
    shutil.copy2(src, dst)
    stats['written'] += 1


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true',
                    help='report drift and exit non-zero; write nothing')
    args = ap.parse_args()

    packs = scan_source()
    labels = read_existing_manifest()
    stats = {'written': 0, 'same': 0, 'removed': 0}

    # Stage the files.
    keep_dirs = set()
    manifest_packs = []
    for slug, icons in packs:
        name, group, keywords = PACKS[slug]
        keep_dirs.add(slug)
        expected = set()
        for num, svg_src, png_src in icons:
            base = '%s-%s' % (slug, num)
            expected.add(base + '.svg')
            expected.add(base + '.png')
            if not args.check:
                copy_if_changed(svg_src, os.path.join(DEST, slug, base + '.svg'), stats)
                copy_if_changed(png_src, os.path.join(DEST, slug, base + '.png'), stats)

        # Drop staged files the source no longer has, so a shrinking pack does not
        # leave orphans that the manifest never references but the zip still ships.
        pack_dir = os.path.join(DEST, slug)
        if os.path.isdir(pack_dir) and not args.check:
            for f in os.listdir(pack_dir):
                if f not in expected and not f.startswith('.'):
                    os.remove(os.path.join(pack_dir, f))
                    stats['removed'] += 1

        entry = {
            'slug': slug,
            'name': name,
            'group': group,
            'count': len(icons),
            'keywords': keywords,
        }
        # Only carry labels that still point at an icon that exists.
        kept = {k: v for k, v in sorted((labels.get(slug) or {}).items())
                if k in {n for n, _, _ in icons}}
        if kept:
            entry['labels'] = kept
        manifest_packs.append(entry)

    # A pack removed from the drop should not linger in assets/, and neither
    # should loose files at the root — every icon now lives inside a pack folder,
    # so anything sitting directly in assets/icons/ is left over from before.
    if os.path.isdir(DEST) and not args.check:
        for d in sorted(os.listdir(DEST)):
            p = os.path.join(DEST, d)
            if os.path.isdir(p):
                if d not in keep_dirs:
                    shutil.rmtree(p)
                    stats['removed'] += 1
                    print('removed stale pack folder assets/icons/%s' % d)
            elif d != 'README.md' and not d.startswith('.'):
                os.remove(p)
                stats['removed'] += 1
                print('removed loose file assets/icons/%s' % d)

    manifest_packs.sort(key=lambda p: (GROUPS.index(p['group']), p['name'].lower()))
    total = sum(p['count'] for p in manifest_packs)

    # Rendered by hand rather than json.dumps(indent=…) so the block stays
    # readable in a diff: one line per pack, and the labels map — the part that is
    # hand-edited — stays on that line with it.
    lines = ['  {',
             '    "version": "3.0",',
             '    "generated": "%s",' % date.today().isoformat(),
             '    "total": %d,' % total,
             '    "packs": [']
    for i, p in enumerate(manifest_packs):
        comma = '' if i == len(manifest_packs) - 1 else ','
        lines.append('      ' + json.dumps(p, ensure_ascii=False) + comma)
    lines += ['    ]', '  }']
    block = '\n'.join(lines)

    text = open(PAGE, encoding='utf-8').read()
    i = text.find(BEGIN)
    j = text.find(END, i + len(BEGIN)) if i >= 0 else -1
    if i < 0 or j < 0:
        die('could not find the manifest block in icons.html. Expected a line\n'
            '       exactly matching:\n       %s' % BEGIN)
    updated = text[:i + len(BEGIN)] + '\n' + block + '\n' + text[j:]

    stale = updated != text
    if args.check:
        print('%d packs, %d icons' % (len(manifest_packs), total))
        if stale:
            print('manifest in icons.html is STALE — run ./tools/icons-sync.py')
            sys.exit(1)
        print('manifest is current')
        return

    if stale:
        open(PAGE, 'w', encoding='utf-8').write(updated)

    label_count = sum(len(p.get('labels', {})) for p in manifest_packs)
    print('%d packs, %d icons across %d groups' % (len(manifest_packs), total, len(GROUPS)))
    print('files: %d written, %d unchanged, %d removed' %
          (stats['written'], stats['same'], stats['removed']))
    print('manifest: %s (%d hand-written labels preserved)' %
          ('rewritten' if stale else 'already current', label_count))
    print('\nNext: ./tools/build-bundles.sh, then commit assets/icons/, icons.html and downloads/.')


if __name__ == '__main__':
    main()
