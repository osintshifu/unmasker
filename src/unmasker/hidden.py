"""Text the document tells its application not to draw.

Word calls it `w:vanish`, OpenDocument `text:display="none"`, and a .doc
stores it as a character property in a table of its own. All three mean what a
PDF render mode that paints neither fill nor stroke means: **these characters
are in the file and not on the page.** So all of them produce `invisible-text`
- the name the PDF detector already uses - rather than one name per container.
A reader who has learned what the finding means in one format should not have
to learn it again in the next.

The readers do the taking-out, not this. A hidden run must never reach
`units`, where it would be searched as though somebody could see it and then
counted as text the document shows - which is worse than missing it, because
a name in a hidden run would make the metadata detector call that name
disclosed.
"""

from __future__ import annotations

from dataclasses import dataclass

from .findings import Basis, Finding, Location


@dataclass(frozen=True)
class HiddenRun:
    """One stretch of text an application was told not to draw."""

    text: str
    part: str = ""
    """Where it was found, named the way the format names it: an archive
    member, or a story in a compound file."""

    mechanism: str = ""
    """What the file used to hide it, in the format's own words."""


def detect(runs) -> list[Finding]:
    """One finding per hidden run."""
    findings = []
    for run in runs:
        count = f"{len(run.text)} character" + ("" if len(run.text) == 1 else "s")
        where = f", in {run.part}" if run.part else ""
        how = f" ({run.mechanism})" if run.mechanism else ""
        findings.append(
            Finding(
                detector="invisible-text",
                basis=Basis.DIRECT,
                summary=(
                    f"{count} the file marks as not to be drawn{how}{where}; no "
                    "print of this document would show them and the characters "
                    "are still in it"
                ),
                human_sees="",
                machine_reads=run.text,
                location=Location(),
            )
        )
    return findings


__all__ = ["HiddenRun", "detect"]
