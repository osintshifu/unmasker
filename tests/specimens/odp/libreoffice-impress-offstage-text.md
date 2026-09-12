# `libreoffice-impress-offstage-text.odp`

**Producer:** LibreOffice 24.2 Impress. The same source as
[`pptx/libreoffice-impress-offstage-text.pptx`](../pptx/libreoffice-impress-offstage-text.pptx),
written by the same script into the other family: one box on the slide, one
parked entirely past its right edge, one overhanging it.

## Why the pair earned its keep

**This file disproved the rule the reader was written with.** The slide size
was taken from the first page layout in `styles.xml` that stated one — and in
a deck the first is the **A4 sheet the notes are laid out on**, 595 × 842
points rather than the slide's 794 × 446. Against that rectangle the
overhanging box looked parked outside, and the detector reported a line that
is plainly on the slide.

The size has to be followed through the chain the file actually states:

```
draw:page  draw:master-page-name="Default"
  style:master-page  style:name="Default"  style:page-layout-name="PM1"
    style:page-layout  style:name="PM1"  fo:page-width="28cm"
```

A slide whose master cannot be resolved is given no size at all, which turns
the check off rather than running it against the wrong rectangle.

Everything in the text and the metadata is invented.
