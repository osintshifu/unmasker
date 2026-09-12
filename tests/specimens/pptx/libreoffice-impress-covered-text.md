# `libreoffice-impress-covered-text.pptx`

**Producer:** LibreOffice 24.2 Impress. Built by
[`sources/build_covered_slide.py`](../sources/build_covered_slide.py), which
writes this and
[`odp/libreoffice-impress-covered-text.odp`](../odp/libreoffice-impress-covered-text.odp)
from one source.

## What a person sees

One slide. Two black bars, a line of text on a black band, and one line in the
clear.

## What is stored inside

Seven shapes, in painting order — and painting order is document order, which
is the whole of the z-order:

| | box (pt) | fill | text |
| ---: | :--- | :--- | :--- |
| 0 | 57, 57, 397, 34 | — | Panel chair: Wanda Testowa-Przyklad |
| 1 | 51, 51, 408, 45 | `#000000` | |
| 2 | 57, 142, 397, 34 | — | Reserve price 250,000 EUR, agreed 12 April. |
| 3 | 57, 142, **198**, 34 | `#000000` | |
| 4 | 57, 227, 397, 34 | `#000000` | |
| 5 | 57, 227, 397, 34 | — | Scores are on the banner, in front of it. |
| 6 | 57, 312, 397, 34 | — | Decision published on 30 April. |

Four cases, and each one exists to pin a different part of the answer:

**Shape 1 contains shape 0.** Every character of that name is behind the bar,
so the evidence is **direct** and the report can say so without qualification.

**Shape 3 takes the left half of shape 2.** The text is partly behind a bar and
the file does not say which part — a slide stores the text *box*, not the
position of each letter. So the finding is **circumstantial** and says why. A
PDF would answer this exactly, because it stores glyph positions; this is the
one thing the slide formats give up.

**Shape 4 is painted before shape 5.** Text on a coloured band is an ordinary
slide. The two rectangles overlap exactly as a redaction does, and the *only*
thing separating them is which was drawn first. This is the false positive
worth a specimen of its own.

**Shape 6 has nothing over it**, and must produce nothing.

## Why this is possible here and not in a `.docx`

A slide states absolute coordinates against a known slide size
(`<p:sldSz cx="10080625" cy="5670550"/>`, EMU, 12700 to the point). A word
processor lays its text out as it flows, so the file never says where the ink
lands; a bar over a paragraph in a `.docx` cannot be found without rendering
the document.

One thing came out of these bytes rather than a specification: **the fill has
to be read from `<p:spPr>` and not from anywhere inside `<p:sp>`.** A
`solidFill` under the shape also matches the colour of the *text* in it, which
would make every text frame look like a bar.

Everything in the text and the metadata is invented.
