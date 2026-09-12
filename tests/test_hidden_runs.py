"""Text a word processor is told not to draw.

Word calls it `w:vanish`, OpenDocument `text:display="none"`, and both mean
what a PDF render mode that paints neither fill nor stroke means: the
characters are in the file and not on the page. Same finding, same detector
name, three containers.

Neither reader looked before this. The hidden run was folded into the body, so
the report said it had searched the text and found nothing hidden - about a
file holding a sentence no print of it would show. And a name in a hidden run
counted as *shown*, which kept the metadata detector quiet about it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from unmasker.detect import collect
from unmasker.readers import read

SPECIMENS = Path(__file__).parent / "specimens"
PAIR = (
    SPECIMENS / "docx" / "libreoffice-writer-hidden-run.docx",
    SPECIMENS / "odt" / "libreoffice-writer-hidden-run.odt",
)


@pytest.mark.parametrize("path", PAIR, ids=lambda p: p.suffix.lstrip("."))
def test_a_hidden_run_is_not_reported_as_text_on_the_page(path):
    extraction = read(path)
    visible = "\n".join(unit.text for unit in extraction.units)
    assert "reserve bidder is Wykonawca B" not in visible
    assert "Panel decision" in visible and "is final." in visible


@pytest.mark.parametrize("path", PAIR, ids=lambda p: p.suffix.lstrip("."))
def test_a_hidden_run_is_the_finding_a_pdf_makes_for_the_same_thing(path):
    findings = [f for f in collect(read(path)) if f.detector == "invisible-text"]
    assert len(findings) == 1
    assert "reserve bidder is Wykonawca B" in findings[0].machine_reads


@pytest.mark.parametrize("path", PAIR, ids=lambda p: p.suffix.lstrip("."))
def test_ordinary_text_still_arrives(path):
    """The filter has to take out the hidden run and nothing else."""
    assert "The contract has been awarded" in "\n".join(
        unit.text for unit in read(path).units
    )
