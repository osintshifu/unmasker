"""Text parked beside a slide rather than on it.

The pasteboard around a slide is working space, and a line dragged onto it is
gone from the projector, the print and the PDF - and still in the shape tree,
still read by anything that walks it. Nobody has to mean anything by it, which
is precisely why it is still there when the deck is sent on.

Two things are being tested, and the second matters more than the first. The
finding is one. The other is that the text stops counting as something an
audience saw: until this landed it went into the extraction as ordinary slide
text, so a name parked off the slide made the metadata detector call that name
disclosed - the same defect already fixed in a .doc and in a .docx.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from unmasker.detect import collect
from unmasker.readers import read

SPECIMENS = Path(__file__).parent / "specimens"
PAIR = (
    SPECIMENS / "pptx" / "libreoffice-impress-offstage-text.pptx",
    SPECIMENS / "odp" / "libreoffice-impress-offstage-text.odp",
)


@pytest.mark.parametrize("path", PAIR, ids=lambda p: p.suffix.lstrip("."))
def test_a_box_parked_beside_the_slide_is_reported(path):
    found = [f for f in collect(read(path)) if f.detector == "off-page-text"]
    assert len(found) == 1
    assert "Wykonawca B" in found[0].machine_reads


@pytest.mark.parametrize("path", PAIR, ids=lambda p: p.suffix.lstrip("."))
def test_a_box_overhanging_the_edge_is_not(path):
    """A title box wider than its slide is ordinary layout, and a slide gives
    no glyph positions - so an overhang cannot be told from a sentence pushed
    half off the edge, and reporting it would fire on decks that hide
    nothing."""
    assert not [
        f
        for f in collect(read(path))
        if f.detector == "off-page-text" and "Overhanging" in f.machine_reads
    ]


@pytest.mark.parametrize("path", PAIR, ids=lambda p: p.suffix.lstrip("."))
def test_text_beside_the_slide_does_not_count_as_text_an_audience_saw(path):
    shown = "\n".join(unit.text for unit in read(path).units)
    assert "Award notice for the panel." in shown
    assert "reserve bidder is Wykonawca B" not in shown
