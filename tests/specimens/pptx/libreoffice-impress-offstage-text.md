# `libreoffice-impress-offstage-text.pptx`

**Producer:** LibreOffice 24.2 Impress. Built by
[`sources/build_offstage_slide.py`](../sources/build_offstage_slide.py), which
writes this and
[`odp/libreoffice-impress-offstage-text.odp`](../odp/libreoffice-impress-offstage-text.odp)
from one source.

## What a person sees

One slide, one line on it. The slide is 794 × 446 points.

## What is stored inside

Three text boxes:

| box (pt) | | |
| :--- | :--- | :--- |
| x 57, width 397 | on the slide | Award notice for the panel. |
| **x 964**, width 397 | entirely past the right edge | Cut from the talk: reserve bidder is Wykonawca B. |
| x 680, width 397 | crosses the edge, partly visible | Overhanging the right edge. |

The pasteboard around a slide is working space. A line dragged onto it is gone
from the projector, the print and the PDF, and still in the shape tree — and
nobody has to have meant anything by it, which is exactly why it is still
there when the deck goes out.

## The third box is what makes the detector usable

A title box wider than its slide is ordinary layout, and a slide gives no
glyph positions — so an overhang cannot be told from a sentence pushed half
off the edge. Reporting it would fire on decks that hide nothing, so **only a
box with no overlap at all** is reported, and this file fails the test if that
ever loosens.

## What the second box cost before this was read

Its text went into the extraction as ordinary slide text, so a name parked
beside the slide counted as something an audience had seen — and
`undisclosed-metadata` stayed quiet about a metadata field naming the same
person. The same defect was fixed in a `.doc` and then in a `.docx`; this is
the third place it lived.

Everything in the text and the metadata is invented.
