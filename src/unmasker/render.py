"""Laying a document out, because some formats will not say where the ink lands.

A slide states absolute coordinates against a known slide size, so a shape
drawn over text is arithmetic. A word processor does not work that way. Its
text has no position at all - it flows, and where it flows depends on the
fonts installed, the page it is being laid out for, and the application doing
the laying out. A `.docx` says *there is a filled shape* and *there is text*
and never says that one is on top of the other.

So the only way to answer the question for those formats is to lay the
document out and look at what got painted. That is what this does: hand the
file to LibreOffice, read back the PDF it produces, and run the detectors that
already know how to look at a painted page.

## What it costs, and why every finding here is circumstantial

**The rendering is not the document.** It is LibreOffice's opinion of what the
document looks like, and Word's opinion differs - different font metrics,
different line breaking, a shape landing a few points to one side. A bar that
covers a name here may miss it there, and the file does not settle it.

The bytes still say something direct: there is a filled shape, and there is
text. What is mediated is the *geometry*. So the findings keep their detector
names and their evidence, and every one of them is downgraded and says which
rendering it came from - a reader who disagrees must be able to see exactly
what they are disagreeing with.

**And it hands the file to another program.** unmasker reads; LibreOffice
parses, and a document built to attack a parser is pointed straight at one.
That is why this is behind a flag that is off by default, and why the promise
on the front page is worded about unmasker rather than about everything it can
be asked to invoke.

## Only what was painted is taken

A rendering has metadata of its own, a producer string of its own and a copy
of the text. Reporting those would describe the conversion instead of the file
somebody asked about, and would say a second time what the document already
said on its own.
"""

from __future__ import annotations

import dataclasses
import shutil
import subprocess
from pathlib import Path

from .findings import Basis, Finding
from .pdf.detectors import detect as detect_drawn

#: What LibreOffice is called, in the order worth trying.
COMMANDS = ("soffice", "libreoffice")

#: Long enough for a document this tool is meant for, short enough that a file
#: which hangs the converter does not hang the report.
PATIENCE = 180

#: The formats whose layout is not in the file. A presentation is not here:
#: its shapes carry coordinates and `unmasker.slides` measures them directly,
#: which is a better answer than a rendering because it is about the file.
FLOWED = ("docx", "odf")

#: Said on every finding that came out of a rendering. It is the difference
#: between "the file says this" and "this is what one application drew".
MEDIATED = (
    " - measured on this document as LibreOffice lays it out rather than on "
    "the file itself, which does not say where its text falls; another "
    "application may place the two differently"
)


def available() -> str | None:
    """The layout program's name, or None where there is none to run."""
    for command in COMMANDS:
        if shutil.which(command):
            return command
    return None


def as_pdf(path: Path, folder: Path) -> tuple[Path | None, list[str]]:
    """Lay `path` out into `folder`, and hand back the PDF.

    The profile is thrown away with the folder. A shared one would let a
    document being examined leave something behind in the profile of the
    person examining it, which is the wrong direction for a tool pointed at
    files somebody else wrote.
    """
    command = available()
    if command is None:
        return None, [
            "this document was not laid out, because LibreOffice was not found "
            "on the path - so nothing here was checked for a shape drawn over "
            "text, which is not the same as checking and finding none"
        ]

    try:
        subprocess.run(
            [
                command, "--headless", "--norestore",
                f"-env:UserInstallation=file://{folder / 'profile'}",
                "--convert-to", "pdf", "--outdir", str(folder), str(path),
            ],
            check=True, capture_output=True, timeout=PATIENCE,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return None, [f"this document could not be laid out, so it was not checked: {exc}"]

    made = folder / f"{path.stem}.pdf"
    if not made.exists():
        return None, [
            "the layout program ran and wrote no PDF, so this document was not "
            "checked for a shape drawn over text"
        ]
    return made, []


def from_layout(extraction) -> list[Finding]:
    """What a rendering paints, reported as being about that rendering."""
    found: list[Finding] = []
    for painted in extraction.drawn:
        for finding in detect_drawn(painted):
            found.append(
                dataclasses.replace(
                    finding,
                    basis=Basis.CIRCUMSTANTIAL,
                    summary=finding.summary + MEDIATED,
                )
            )
    return found


__all__ = ["FLOWED", "as_pdf", "available", "from_layout"]
