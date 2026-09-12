# `libreoffice-impress-covered-text.odp`

**Producer:** LibreOffice 24.2 Impress. The same source as
[`pptx/libreoffice-impress-covered-text.pptx`](../pptx/libreoffice-impress-covered-text.pptx),
written by the same script into the other family, and holding the same four
cases: a box covered whole, a box covered in part, text on a banner, and text
in the clear.

## What the pair is for

**OpenDocument keeps the fill a step away from the shape.** The shape carries
`draw:style-name="gr2"` and the style carries
`draw:fill="solid" draw:fill-color="#000000"`, so the styles have to be read
before any shape on the page means anything. OOXML writes the fill on the
shape itself.

**And it writes a measurement, not a count.** `svg:x="1.8cm"` against OOXML's
`<a:off x="720000"/>` in EMU — so the unit has to be parsed rather than
divided, and a unit this reader does not know is refused rather than guessed
at and silently placed somewhere wrong.

The slide size is in the page layout, which lives in `styles.xml` for a file
written as a package and in `content.xml` for one written flat. Both are
tried, because the size is what says whether a fill is a bar or the slide's
own background.

Everything in the text and the metadata is invented.
