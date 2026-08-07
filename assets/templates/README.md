# Templates & decks

**No template files live in this folder, and that is the design.** Every row on
`templates.html` links to SharePoint instead.

SharePoint holds the copies that actually get updated. A duplicate in this repo would go
stale the first time someone revised the original, and nobody would notice — the same
failure mode the zip bundles have, except a bundle at least gets rebuilt by a script
someone runs, and a forgotten copy of a deck gets nothing. A link is always current; a
copy is only current by luck.

## Adding a template

1. Put the file in the appropriate SharePoint templates folder — for the DXC team that is
   [Strategy/Templates](https://rbaconsulting.sharepoint.com/sites/rba_digital_experience_and_commerce/Shared%20Documents/Strategy/Templates).
2. Add a `<tr>` to the table in `templates.html`: name, one-line note, format, scope
   (Company-wide or the owning team), the file's real last-modified date, and a link.

The table is plain HTML rather than a manifest — there are only ever a handful of rows, and
hand-writing it means the page works with JavaScript off.

**Put the real date in.** That column is what makes staleness visible: the consultant
profile reads "30 Apr 2021", which is how you can tell at a glance that it predates the
2026 brand.

## Scope matters

A company-wide master and one team's working spreadsheet can both be useful, but they are
not the same thing, and conflating them is how a team's internal estimate sheet ends up in
front of a client. Mark every row.

## What is stocked

Company-wide: the PowerPoint master, the consultant 1-page profile.
DXC team: stakeholder interview deck, measurement strategy, estimate spreadsheet, event
tracking and UTM schema.

Searched and **not found** as of August 2026: a letterhead, a client proposal deck, and a
case study document. Rows for those three existed here as scaffolding placeholders and were
removed rather than left implying files that don't exist. If any get made, they belong in
the company-wide group.

## Fonts

The canonical project bundles the brand-approved TTFs (20 Montserrat cuts, 3 Libre Caslon
Text) under its own `fonts/` folder and loads them with `@font-face`. This site instead
loads both faces from Google Fonts, because they are the same open-licensed families and a
CDN link needs no files in the repo.

If a **font download** is ever wanted here — someone installing Montserrat locally to build
a deck — copy the 23 TTFs across from the design-system project into `assets/fonts/`, add a
collection to `tools/build-bundles.sh`, and list it on this page. They were not imported
automatically: they are binaries, they are already available from Google Fonts, and nothing
on this site renders differently without them.
