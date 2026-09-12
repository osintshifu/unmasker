"""DOCX body text, for the detectors that only need characters.

This reads what a reader *sees*: the `w:t` runs of the document body, its
headers and its footers. It deliberately does not read `w:delText`, the deleted
text that tracked changes leave inside the file - folding that in here would
report it as ordinary body text, which is the opposite of what it is. It is
read separately, by `unmasker.ooxml.revisions`, which keeps the author and the
date attached to it; the record comes back on the extraction.

A run carrying `w:vanish` is kept out of the body for the same reason. Word
does not draw it and no print of the document shows it, so folding it in would
have the report say it had searched the text and found nothing hidden - about
a file holding a sentence nobody can see. Worse, a name in a hidden run would
count as shown, and the metadata detector would stay quiet about it. Those
runs come back separately and become `invisible-text`.

No new dependency: a DOCX is a zip of XML, and both are in the standard library.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree import ElementTree

from ..hidden import HiddenRun
from ..metadata import read_ooxml
from ..metadata.detectors import describe
from ..ooxml.revisions import read_revisions
from .model import Extraction, TextUnit, UnreadableFile

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _parts(archive: zipfile.ZipFile) -> list[str]:
    """Body first, then headers and footers, in a stable order."""
    names = set(archive.namelist())
    ordered = ["word/document.xml"] if "word/document.xml" in names else []
    ordered += sorted(
        n for n in names if n.startswith(("word/header", "word/footer")) and n.endswith(".xml")
    )
    return ordered


def _vanished(run) -> bool:
    """Whether Word was told not to draw this run.

    `w:vanish` is a toggle, so it can be switched back off by a `w:val` of
    false - a run that inherits hiding from its style and overrides it is
    visible, and reporting it would be this tool inventing a finding.
    """
    properties = run.find(f"{W}rPr")
    if properties is None:
        return False
    toggle = properties.find(f"{W}vanish")
    if toggle is None:
        return False
    return toggle.get(f"{W}val", "true") not in ("0", "false", "off")


def _text_of(xml: bytes) -> tuple[str, list[str]]:
    """Paragraph text one paragraph per line, and the runs Word does not draw.

    Tabs become tabs and `w:br` becomes a newline, so a column of values does
    not collapse into one run and report a column number a reader cannot find.
    """
    root = ElementTree.fromstring(xml)
    lines: list[str] = []
    hidden: list[str] = []
    for para in root.iter(f"{W}p"):
        buf: list[str] = []
        for run in para.iter(f"{W}r"):
            out = []
            for node in run.iter():
                if node.tag == f"{W}t":
                    out.append(node.text or "")
                elif node.tag == f"{W}tab":
                    out.append("\t")
                elif node.tag == f"{W}br":
                    out.append("\n")
            if _vanished(run):
                hidden.append("".join(out))
            else:
                buf.append("".join(out))
        lines.append("".join(buf))
    return "\n".join(lines), hidden


def read_docx(path: Path) -> Extraction:
    try:
        archive = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as exc:
        raise UnreadableFile(f"{path.name} is not a readable zip: {exc}") from exc

    with archive:
        names = archive.namelist()
        if "word/document.xml" not in names:
            hint = ""
            if "content.xml" in names:
                # It has been read since the ODF reader landed. A message that
                # tells a user the tool cannot do something it can is disproved
                # by the first thing they try, and everything else on the
                # screen loses credibility with it.
                hint = "; it looks like an OpenDocument file - pass it to unmasker directly"
            raise UnreadableFile(f"{path.name} is a zip but not a Word document{hint}")

        units: list[TextUnit] = []
        remarks: list[str] = []
        hidden: list[HiddenRun] = []
        for name in _parts(archive):
            try:
                text, unseen = _text_of(archive.read(name))
            except ElementTree.ParseError as exc:
                remarks.append(f"{name} is not well-formed XML and was skipped: {exc}")
                continue
            if text.strip():
                units.append(TextUnit(text=text))
            hidden.extend(
                HiddenRun(text=run, part=name, mechanism="w:vanish")
                for run in unseen
                if run.strip()
            )

        record = read_revisions(archive)
        remarks.extend(record.remarks)

        metadata = read_ooxml(archive)
        remarks.extend(metadata.remarks)
        remarks.extend(describe(metadata))

        if not units:
            remarks.append("the document body holds no text, so there was nothing to search")

    return Extraction(
        kind="docx",
        units=tuple(units),
        remarks=tuple(remarks),
        revisions=record,
        hidden=tuple(hidden),
        metadata=metadata,
    )
