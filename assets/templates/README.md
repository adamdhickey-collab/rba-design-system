# Templates & decks

Empty. **No template files are stocked yet** — every row on `templates.html` shows
"Not yet stocked".

## Adding a template

1. Drop the file in this folder (`.pptx`, `.docx`, `.potx`, `.dotx`, `.xlsx`).
2. Edit the row in `templates.html`.

Unlike the icon and image grids, this page is **plain HTML, not rendered from a
manifest**. There are only ever a handful of templates, a `<tr>` is no harder to
edit than a JSON row, and hand-writing it means the table and its download links
work with JavaScript switched off.

To stock a row, replace:

```html
<td><span class="file-pending">Not yet stocked</span></td>
```

with:

```html
<td>
  <a class="btn btn-secondary btn--sm" href="assets/templates/rba-presentation.pptx" download>
    <span class="material-symbols-rounded" aria-hidden="true">download</span>
    <span>Download</span>
  </a>
</td>
```

Then fill in the Size and Updated cells, and delete `data-status="pending"` from
the `<tr>`.

## Before you upload a template

The template is what everyone else's work inherits, so the checks matter more here
than anywhere else in this repo:

- **Fonts:** Montserrat throughout, Libre Caslon Text only for editorial display.
  Don't leave a theme font set to Calibri.
- **Theme palette:** the file's own theme colors should be the RBA palette, so
  someone using the built-in picker lands on brand colors by default.
- **Layouts:** build real master layouts. If people have to paste free text boxes
  onto blank slides, the template isn't doing its job.
- **Strip the content:** no client names, no pricing, no notes from the deck you
  built it from. Check the speaker notes and the document properties too.

## After adding templates

```bash
./tools/build-bundles.sh
```
