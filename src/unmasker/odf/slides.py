"""An OpenDocument presentation's slides, and which of them are skipped.

The same indirection this format uses for a hidden spreadsheet sheet, one
container over: **a slide's visibility is not on the slide**. The page names a
style, and the style, elsewhere in the file, says
`presentation:visibility="hidden"`.

    <draw:page draw:name="Cut" draw:style-name="dp3">
    ...
    <style:style style:name="dp3" style:family="drawing-page">
      <style:drawing-page-properties presentation:visibility="hidden"/>

A reader that looks for an attribute on the page finds nothing and reports a
deck with a cut slide as clean. Having met it once in `odf/sheets.py` is the
only reason it was expected here.

Notes sit inside the slide they belong to, in `<presentation:notes>`, which is
the same shape as an annotation inside a paragraph and carries the same trap:
walking the subtree naively puts the speaker's private line into the text of
the slide itself.

No new dependency: an .odp is a zip of XML and both are in the standard
library.
"""

from __future__ import annotations

import zipfile
from xml.etree import ElementTree

from ..slides import Shape, Slide, SlideRecord

OFFICE = "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}"
DRAW = "{urn:oasis:names:tc:opendocument:xmlns:drawing:1.0}"
PRESENTATION = "{urn:oasis:names:tc:opendocument:xmlns:presentation:1.0}"
STYLE = "{urn:oasis:names:tc:opendocument:xmlns:style:1.0}"
TEXT = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"
SVG = "{urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0}"
FO = "{urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0}"

#: Points per unit. OpenDocument writes a real measurement with its unit
#: attached, where OOXML writes a count of EMU - so this has to parse rather
#: than divide, and a unit it does not know is refused rather than guessed at.
UNITS = {"pt": 1.0, "in": 72.0, "cm": 72.0 / 2.54, "mm": 7.2 / 2.54, "pc": 12.0}

#: The shapes a slide can be built from. `draw:frame` holds a text box or an
#: image; the rest are drawn figures, and a filled one of those is what
#: somebody reaches for to cover a name.
FIGURES = (
    f"{DRAW}frame", f"{DRAW}rect", f"{DRAW}custom-shape",
    f"{DRAW}ellipse", f"{DRAW}circle", f"{DRAW}polygon", f"{DRAW}path",
)


def _hidden_styles(root) -> set[str]:
    """Style names whose pages are skipped. The indirection this reader exists
    for."""
    names = set()
    for container in (f"{OFFICE}automatic-styles", f"{OFFICE}styles"):
        for holder in root.iter(container):
            for style in holder.iter(f"{STYLE}style"):
                if style.get(f"{STYLE}family") != "drawing-page":
                    continue
                for props in style.iter(f"{STYLE}drawing-page-properties"):
                    if (props.get(f"{PRESENTATION}visibility") or "").strip() == "hidden":
                        name = style.get(f"{STYLE}name")
                        if name:
                            names.add(name)
    return names


def _points(value: str | None) -> float | None:
    """A measurement in points, or None where it is not one this understands."""
    if not value:
        return None
    text = value.strip()
    for unit, factor in UNITS.items():
        if text.endswith(unit):
            try:
                return float(text[: -len(unit)]) * factor
            except ValueError:
                return None
    return None


def _fills(root) -> dict[str, str]:
    """Which graphic style names paint a solid fill, and in what colour.

    OpenDocument keeps this a step away from the shape: the shape carries a
    style name and the style carries the fill, so the styles have to be read
    before any shape on the page means anything. Word's slides put it on the
    shape.
    """
    out: dict[str, str] = {}
    for style in root.iter(f"{STYLE}style"):
        name = style.get(f"{STYLE}name")
        if not name or style.get(f"{STYLE}family") not in ("graphic", "presentation"):
            continue
        for props in style.iter(f"{STYLE}graphic-properties"):
            if (props.get(f"{DRAW}fill") or "none") == "none":
                continue
            out[name] = props.get(f"{DRAW}fill-color") or "solid"
    return out


def _shapes(page, fills: dict[str, str], skip: set[int]) -> list[Shape]:
    """Every placed figure on the page, in the order the file paints it.

    Document order is painting order here as it is in OOXML. A figure without
    a full set of coordinates is left out rather than placed at the origin,
    where it would sit under everything and be reported as covered by it.
    """
    found: list[Shape] = []
    for index, node in enumerate(n for n in page.iter() if n.tag in FIGURES):
        if id(node) in skip:
            continue
        box = [
            _points(node.get(f"{SVG}x")),
            _points(node.get(f"{SVG}y")),
            _points(node.get(f"{SVG}width")),
            _points(node.get(f"{SVG}height")),
        ]
        if any(value is None for value in box):
            continue

        style = node.get(f"{DRAW}style-name") or node.get(f"{PRESENTATION}style-name") or ""
        found.append(
            Shape(
                left=box[0], top=box[1], width=box[2], height=box[3],  # type: ignore[arg-type]
                order=index,
                text="\n".join(_paragraphs(node, skip)),
                fill=fills.get(style, ""),
            )
        )
    return found


def _page_size(root) -> tuple[float, float]:
    """The slide, in points, out of the first page layout that states one."""
    for props in root.iter(f"{STYLE}page-layout-properties"):
        width, height = _points(props.get(f"{FO}page-width")), _points(
            props.get(f"{FO}page-height")
        )
        if width and height:
            return width, height
    return 0.0, 0.0


def _paragraphs(node, skip: set[int]) -> list[str]:
    out = []
    for paragraph in node.iter(f"{TEXT}p"):
        if id(paragraph) in skip:
            continue
        text = "".join(paragraph.itertext()).strip()
        if text:
            out.append(text)
    return out


def _read_page(page, hidden: bool, number: int, fills, size) -> Slide:
    # The notes subtree is taken out of the slide's own text first. Walking it
    # naively puts the speaker's private line into what the audience saw.
    notes_nodes = list(page.iter(f"{PRESENTATION}notes"))
    inside_notes = {id(n) for node in notes_nodes for n in node.iter()}

    on_screen = _paragraphs(page, inside_notes)
    spoken: list[str] = []
    for node in notes_nodes:
        spoken.extend(_paragraphs(node, set()))

    return Slide(
        number=number,
        text="\n".join(on_screen),
        notes="\n".join(spoken),
        hidden=hidden,
        title=on_screen[0] if on_screen else page.get(f"{DRAW}name"),
        shapes=tuple(_shapes(page, fills, inside_notes)),
        width=size[0],
        height=size[1],
    )


def read_slides(archive: zipfile.ZipFile) -> SlideRecord:
    if "content.xml" not in archive.namelist():
        return SlideRecord(remarks=("the file has no content.xml and was not read",))

    try:
        root = ElementTree.fromstring(archive.read("content.xml"))
    except ElementTree.ParseError as exc:
        return SlideRecord(remarks=(f"content.xml is not well-formed XML: {exc}",))

    invisible = _hidden_styles(root)
    fills = _fills(root)
    size = _page_size(root)
    if not size[0]:
        # The layout lives in styles.xml for a file written as a package,
        # and in content.xml for one written flat.
        try:
            size = _page_size(ElementTree.fromstring(archive.read("styles.xml")))
            fills.update(_fills(ElementTree.fromstring(archive.read("styles.xml"))))
        except (KeyError, ElementTree.ParseError):
            size = (0.0, 0.0)

    slides: list[Slide] = []
    for body in root.iter(f"{OFFICE}presentation"):
        for page in body.iter(f"{DRAW}page"):
            hidden = (page.get(f"{DRAW}style-name") or "") in invisible
            slides.append(_read_page(page, hidden, len(slides) + 1, fills, size))

    return SlideRecord(slides=tuple(slides))
