"""Looking at what a word processor paints, because the file will not say.

A slide states absolute coordinates and the overlap is arithmetic. A word
processor lays its text out as it flows: the shape has an anchor and an
offset, the text has no position at all, and where the two meet is decided by
whichever application opens the document. The file is not the arbiter, so
nothing read out of it can answer the question.

Laying the document out and looking at what got painted can. That is what
`--render` does, and the cost is that the answer is now about **a** rendering
rather than about the file - so every finding it produces is circumstantial
and says which rendering it came from.

The split here is deliberate. The part that decides what to report is pure and
runs on every platform, against a committed PDF standing in for a rendering.
Only the part that shells out to LibreOffice is skipped where LibreOffice is
absent, which is every CI runner - a test that skipped in both halves would
leave the whole feature unchecked everywhere.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from unmasker.findings import Basis
from unmasker.readers import read
from unmasker.render import as_pdf, from_layout

SPECIMENS = Path(__file__).parent / "specimens"
BARS = SPECIMENS / "pdf" / "libreoffice-writer-black-bars.pdf"
FLOWED = (
    SPECIMENS / "docx" / "libreoffice-writer-covered-text.docx",
    SPECIMENS / "odt" / "libreoffice-writer-covered-text.odt",
)


# --- the part that runs everywhere -----------------------------------------


def test_what_a_rendering_paints_is_reported_as_being_about_the_rendering():
    """The bars specimen stands in for a laid-out document here. What matters
    is that nothing coming out of a rendering keeps a direct basis: the shape
    covers those glyphs in *this* layout, and the file did not say so."""
    found = from_layout(read(BARS))
    assert found, "the rendering painted bars over text and produced nothing"
    assert {f.basis for f in found} == {Basis.CIRCUMSTANTIAL}
    assert all("lays it out" in f.summary for f in found)
    assert any("Wanda Testowa-Przyklad" in f.machine_reads for f in found)


def test_only_what_was_painted_is_taken_from_a_rendering():
    """A rendering has its own metadata, its own producer string and its own
    text. Reporting those would describe the conversion rather than the file
    the reader was asked about, and would double every finding the document
    already produced on its own."""
    assert {f.detector for f in from_layout(read(BARS))} <= {
        "covered-text",
        "text-under-image",
        "invisible-text",
        "low-contrast-text",
        "off-page-text",
    }


# --- the part that needs LibreOffice ---------------------------------------

layout = pytest.mark.skipif(
    not (shutil.which("soffice") or shutil.which("libreoffice")),
    reason="needs LibreOffice to lay a document out",
)


@layout
@pytest.mark.parametrize("path", FLOWED, ids=lambda p: p.suffix.lstrip("."))
def test_a_bar_over_text_is_found_only_once_the_document_is_laid_out(path, tmp_path):
    """Reading the markup finds nothing here, and correctly: the .docx says
    there is a filled shape and it says there is text, and it does not say
    that one is on top of the other."""
    from unmasker.detect import collect

    assert not [f for f in collect(read(path)) if f.detector == "covered-text"]

    rendered, problems = as_pdf(path, tmp_path)
    assert rendered is not None, problems
    covered = [f for f in from_layout(read(rendered)) if f.detector == "covered-text"]
    assert covered
    assert any("250,000 EUR" in f.machine_reads for f in covered)


@layout
def test_the_flag_reaches_the_document_through_the_pipeline():
    """The two tests above call the pieces directly, and a bug walked straight
    through the gap between them: a .docx reader that did not remember the
    file it read, so the branch that lays the document out never ran and the
    flag did nothing at all."""
    from unmasker.detect import examine

    findings = examine(read(FLOWED[0]), render=True).findings
    assert [f for f in findings if f.detector == "covered-text"]


@layout
def test_a_document_that_was_not_laid_out_says_so(monkeypatch):
    """The note is the point of the feature as much as the finding is. Without
    LibreOffice nothing was checked, and a report that stays silent about that
    is claiming a search it did not run."""
    import unmasker.render as module
    from unmasker.detect import examine

    monkeypatch.setattr(module, "available", lambda: None)
    analysis = examine(read(FLOWED[0]), render=True)
    findings, notes = analysis.findings, analysis.notes
    assert not [f for f in findings if f.detector == "covered-text"]
    assert any("LibreOffice was not found" in note for note in notes)
