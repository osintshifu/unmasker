"""Running every detector over one reading of one file.

This was inside `cli.py` while the command line was its only caller. The
directory survey is a second one, and a module that imports the command line to
borrow one function is a cycle waiting for the command line to import it back.

Nothing here decides how anything is printed. It answers *what does this file
disagree with itself about*, once, for whoever is asking.

**Notes come back with the findings.** Several detectors learn something about
their own coverage while running - a page that could not be rendered, a tool
that is not installed, a document that could not be laid out - and that is the
difference between *searched and nothing there* and *nothing looked*, which is
the distinction this whole tool is built on. Returning only the findings
throws every one of those sentences away.

**And one bit says whether it ran at all.** A note is prose; nothing can act
on it. `Analysis.complete` is the same fact in a form the exit code can use,
and it is set where the gap is known rather than recovered afterwards by
reading the notes back - a string match on "could not" is not a contract.

It is deliberately one bit and not a status per detector. Which check did not
run is a question the report already answers in words, and a second machine
channel is easy to add later and hard to take away.
"""

from __future__ import annotations

import dataclasses

from .attachments import detect_attachments
from .findings import Finding
from .hidden import detect as detect_hidden
from .metadata.detectors import detect as detect_metadata
from .pdf.detectors import detect as detect_drawn
from .pdf.detectors import unextractable_text, unrendered_text
from .pdf.history import detect as detect_earlier
from .pdf.rendered import read_page_back
from .render import FLOWED, as_pdf, from_layout
from .revisions import detect as detect_revisions
from .sheets import detect as detect_sheets
from .slides import detect as detect_slides
from .text.invisible import scan_text
from .thumbnails import detect as detect_thumbnails


@dataclasses.dataclass(frozen=True)
class Analysis:
    """One reading of one file, and whether the reading finished.

    `complete` is false when a check that should have run did not: a format
    whose hiding mechanisms have no reader, a text layer left undecoded, or an
    external step the caller asked for that failed. It is never false merely
    because nothing was found.
    """

    findings: tuple[Finding, ...] = ()
    notes: tuple[str, ...] = ()
    complete: bool = True


def collect(extraction, ocr: bool = False, render: bool = False) -> list[Finding]:
    """What this file disagrees with itself about."""
    return list(examine(extraction, ocr, render).findings)


def examine(extraction, ocr: bool = False, render: bool = False) -> Analysis:
    """That, what the detectors could not do, and whether they all ran.

    Two entry points rather than one because almost every caller wants the
    findings and nothing else, and a report is the one that must also say
    where a detector was unable to look.
    """
    return _collect(extraction, ocr, render, descend=True)


def _inside(attachments: tuple) -> tuple[list[Finding], list[str], bool]:
    """Everything a carried office package holds, read as a document itself.

    A spreadsheet inside a report hides a sheet exactly as one on disk does,
    and the file a person was sent is the one carrying it. Nothing was looking
    until now.

    One level only. A package inside a package is not descended into, because
    a document that carries itself would otherwise be read forever, and the
    remark says so rather than letting the depth pass for coverage.

    Completeness comes back with the findings. A carried workbook that could
    not be fully checked leaves the carrying document not fully checked too -
    the person was sent one file, and what is inside it is inside it.
    """
    import tempfile
    from pathlib import Path

    from .readers import UnreadableFile, UnsupportedDocument
    from .readers import read as read_file

    found: list[Finding] = []
    notes: list[str] = []
    complete = True
    for carried in attachments:
        if not carried.data:
            continue
        # A directory rather than `NamedTemporaryFile`: Windows will not let a
        # second handle open a named temporary that is still open, so the read
        # below failed there and the `except` swallowed it. Three CI jobs found
        # nothing and said nothing, which is the failure this tool is against.
        with tempfile.TemporaryDirectory(prefix="unmasker-carried-") as folder:
            written = Path(folder) / "carried"
            written.write_bytes(carried.data)
            try:
                inner = read_file(written)
            except UnsupportedDocument:
                # A zip this tool does not read as a document. That it is there
                # has already been said by `detect_attachments`.
                continue
            except UnreadableFile as exc:
                complete = False
                notes.append(f"embedded file {carried.name!r} could not be checked: {exc}")
                continue
            analysis = _collect(inner, ocr=False, descend=False)
            complete = complete and analysis.complete
            if not analysis.complete:
                notes.append(f"embedded file {carried.name!r} was not fully checked")
                for reason in (*inner.unsearched, *analysis.notes):
                    notes.append(f"in embedded file {carried.name!r}: {reason}")
            for finding in analysis.findings:
                found.append(
                    dataclasses.replace(
                        finding,
                        location=dataclasses.replace(
                            finding.location, inside=carried.name
                        ),
                    )
                )
    return found, notes, complete


def _collect(extraction, ocr: bool = False, render: bool = False, *, descend: bool = True):
    """Run every text detector over every unit, tagging findings with the page.

    Detectors are additive and none outranks another: a unit with a bidi
    override and a homoglyph produces two findings, and nothing here filters
    one against the other.
    """
    found: list[Finding] = []
    notes: list[str] = []

    # Two coverage facts the reader established and this layer only carries:
    # a container whose own hiding mechanisms nothing here reads, and a text
    # layer that went undecoded. Either one means a check that belongs to this
    # file was never made.
    complete = not extraction.unsearched and not extraction.text_unread

    for unit in extraction.units:
        for finding in scan_text(unit.text):
            if unit.page is not None:
                finding = dataclasses.replace(
                    finding,
                    location=dataclasses.replace(finding.location, page=unit.page),
                )
            found.append(finding)

    # Tier 1, for readers that can see what is painted. A page with a bar over
    # its text *and* a zero-width character in it has two findings, and neither
    # is allowed to suppress the other.
    for painted in extraction.drawn:
        found.extend(detect_drawn(painted))

    # Tier 4, for readers that can see what an application agreed not to show.
    if extraction.revisions is not None:
        found.extend(detect_revisions(extraction.revisions))

    # The same statement in a workbook: a row, a column or a sheet that carries
    # an attribute saying not to draw it, and every value in it still in the
    # file.
    if extraction.sheets is not None:
        found.extend(detect_sheets(extraction.sheets))

    # The same statement in a deck: a slide an application skips, and a note
    # that was never on the screen at all.
    if extraction.slides is not None:
        found.extend(detect_slides(extraction.slides))

    # Text the document marks as not to be drawn: `w:vanish` in a .docx,
    # `text:display="none"` in an .odt, a character property in a .doc. One
    # statement, so one detector, whichever container it arrives in.
    if extraction.hidden:
        found.extend(detect_hidden(extraction.hidden))

    # A photograph, against the smaller photograph inside it. The shape
    # comparison is free; reading the preview back costs an OCR pass and waits
    # for --ocr, like everything else that renders.
    if extraction.image is not None and extraction.source is not None:
        pictured, problems = detect_thumbnails(extraction.source, extraction.image, ocr=ocr)
        found.extend(pictured)
        notes.extend(problems)
        # Only reachable with --ocr, so a problem here is a check the caller
        # asked for and did not get.
        complete = complete and not problems

    # A word processor does not say where its text falls, so the only way to
    # ask whether a shape is drawn over any of it is to lay the document out
    # and look. That hands the file to another program, which is why it waits
    # to be asked for; every finding it makes says which rendering it is about.
    if render and extraction.source is not None and extraction.kind in FLOWED:
        import tempfile
        from pathlib import Path

        from .readers import read as read_file

        with tempfile.TemporaryDirectory(prefix="unmasker-layout-") as folder:
            laid, problems = as_pdf(Path(str(extraction.source)), Path(folder))
            notes.extend(problems)
            complete = complete and laid is not None and not problems
            if laid is not None:
                found.extend(from_layout(read_file(laid)))

    # Reading each page back costs a render and an OCR pass - seconds a page -
    # and needs two external binaries, which is why it was kept out
    # of the first version and is still off unless asked for.
    if ocr and extraction.source is not None:
        for painted in extraction.drawn:
            words, problems = read_page_back(extraction.source, painted.number, painted.box)
            notes.extend(problems)
            # One page that would not render leaves the rest of the document
            # read and this page unasked. That is not a clean page.
            complete = complete and not problems
            found.extend(unrendered_text(painted, words))
            found.extend(unextractable_text(painted, words))

    # Everything the current catalogue stopped pointing at. A PDF is appended
    # to rather than rewritten, so an edit leaves what it replaced in the file.
    if extraction.earlier:
        shown = "\n".join(unit.text for unit in extraction.units)
        found.extend(detect_earlier(extraction.earlier, shown))

    # A whole file carried inside this one. Not a hiding technique - an
    # attachment is a feature - but it is content the page does not mention,
    # which is the same statement as every other detector here.
    if extraction.attachments:
        found.extend(detect_attachments(extraction.attachments))
        # Saying a workbook is there and reading what is in it are two
        # findings, not a ranking. Both are reported.
        if descend:
            carried, carried_notes, carried_complete = _inside(extraction.attachments)
            found.extend(carried)
            notes.extend(carried_notes)
            complete = complete and carried_complete

    # Metadata is only a finding where it says something the document does not,
    # so the detector is given the document's own text to compare against.
    if extraction.metadata is not None:
        shown = "\n".join(unit.text for unit in extraction.units)
        found.extend(
            detect_metadata(
                extraction.metadata, shown, comparable=not extraction.text_unread
            )
        )

    return Analysis(
        findings=tuple(sorted(found, key=lambda f: f.location.sort_key)),
        notes=tuple(notes),
        complete=complete,
    )
