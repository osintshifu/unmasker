# `libreoffice-writer-covered-text.docx`

**Producer:** LibreOffice 24.2 Writer. Built by
[`sources/build_covered_flowed.py`](../sources/build_covered_flowed.py), which
writes this and
[`odt/libreoffice-writer-covered-text.odt`](../odt/libreoffice-writer-covered-text.odt)
from one source.

## What a person sees

Three lines, the middle one behind a black bar.

## What is stored inside

A filled rectangle, and the sentence it covers:

> Reserve price is 250,000 EUR and must not leave the panel.

## Why this file is different from every other covered-text specimen

**The document does not say the bar is over anything.** It says there is a
filled shape, anchored to a paragraph with an offset. It says there is text.
It never says where that text falls, because a word processor lays its text out
as it flows — the fonts installed, the page size and the application all decide
it, and two applications can disagree.

A PDF stores the glyph at a coordinate. A slide states a shape's box against a
known slide size. This format states neither, so nothing read out of it can
answer the question. `--render` lays the document out and looks at what got
painted, and every finding it makes says so.

## The offset was chosen by rendering, not by arithmetic

The first version of this script put the bar at `svg:y="-0.55cm"`, which reads
like "just above the paragraph it belongs to". After the round trip through
`.docx` it covered the paragraph *above* that one — the award notice, not the
price.

That is the specimen making its own argument. The same number means different
things once an application has laid the file out, and the only way to know
which is to lay it out and look.

Everything in the text and the metadata is invented.
