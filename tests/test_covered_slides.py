"""A shape drawn over text on a slide.

The oldest failed redaction there is, and until now it worked on PDF alone.
A slide can be checked without rendering anything, because unlike a word
processor it says exactly where every shape is: absolute coordinates against a
known slide size, painted in document order.

What it does not say is where each character sits inside its text box. A PDF
gives glyph positions, so its detector names the 22 characters under the bar
and quotes the rest of the line. The smallest thing with a position here is
the whole box, so the claim is only as strong as the geometry supports - whole
box covered is direct, part of it is circumstantial, and the finding says so.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from unmasker.detect import collect
from unmasker.findings import Basis
from unmasker.readers import read

SPECIMENS = Path(__file__).parent / "specimens"
PAIR = (
    SPECIMENS / "pptx" / "libreoffice-impress-covered-text.pptx",
    SPECIMENS / "odp" / "libreoffice-impress-covered-text.odp",
)


def covered(path):
    return [f for f in collect(read(path)) if f.detector == "covered-text"]


@pytest.mark.parametrize("path", PAIR, ids=lambda p: p.suffix.lstrip("."))
def test_a_box_the_bar_contains_is_reported_as_directly_covered(path):
    found = [f for f in covered(path) if f.basis is Basis.DIRECT]
    assert len(found) == 1
    assert found[0].machine_reads == "Panel chair: Wanda Testowa-Przyklad"


@pytest.mark.parametrize("path", PAIR, ids=lambda p: p.suffix.lstrip("."))
def test_a_box_the_bar_only_half_covers_is_not_claimed_as_certainly_hidden(path):
    """The file does not say which characters are behind the bar, so the
    finding must not read as though it did."""
    found = [f for f in covered(path) if f.basis is Basis.CIRCUMSTANTIAL]
    assert len(found) == 1
    assert "250,000 EUR" in found[0].machine_reads


@pytest.mark.parametrize("path", PAIR, ids=lambda p: p.suffix.lstrip("."))
def test_text_painted_on_top_of_a_filled_shape_is_not_a_finding(path):
    """Text on a coloured band is an ordinary slide. The shapes overlap exactly
    as a redaction does and only the painting order tells them apart."""
    assert not [f for f in covered(path) if "banner" in f.machine_reads]


@pytest.mark.parametrize("path", PAIR, ids=lambda p: p.suffix.lstrip("."))
def test_text_with_nothing_over_it_is_not_a_finding(path):
    assert not [f for f in covered(path) if "30 April" in f.machine_reads]
