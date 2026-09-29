"""Anything that is already text: TXT, Markdown, source code, CSV.

Tier 2 needs nothing else from these files. The characters it hunts are in the
bytes, and no container has to be understood first.

## Text is not the same as *only* text

Three formats arrive here that decode perfectly and are not plain text at all.
An HTML file yields every word to any decoder, and `display:none`,
`font-size:0`, white-on-white and `position:absolute;left:-9999px` are
invisible to all of them. RTF has `\\v`, which marks a run as hidden. An SVG
can set `opacity="0"` on a `<text>` element.

Reading one of those and reporting it searched is the one thing this tool must
never do: it states what the evidence does not support, in the direction that
matters, on exactly the kind of file a retrieval pipeline is fed. So they are
recognised, read for what the character detectors can do, and named on
`unsearched` - which is what stops the analysis being called complete and the
exit code being 0.

The recognition is deliberately conservative and structural. It asks what the
document *is* - the first thing in it after the declarations - and never
whether a tag appears somewhere inside. A note quoting `<div>` is still a note,
and a rule that called it HTML would turn every file of prose about HTML into
an incomplete analysis. A false `incomplete` teaches a reader to ignore the
field, which costs more than the case it catches.
"""

from __future__ import annotations

import re
from pathlib import Path

from .model import Extraction, TextUnit, UnreadableFile

#: Declarations that may precede the root element and say nothing about what
#: the document is: an XML declaration, a comment, a processing instruction.
_PREAMBLE = re.compile(r"\s*(?:<\?[^>]*\?>|<!--.*?-->)\s*", re.S)

#: `<!DOCTYPE html ...>`, whose name is the document type outright.
_DOCTYPE = re.compile(r"\s*<!DOCTYPE\s+([A-Za-z][\w.-]*)[^>]*>", re.I | re.S)

#: The first element actually opened.
_ROOT = re.compile(r"\s*<\s*([A-Za-z][\w:.-]*)")

#: What each format is called and how it hides text. The article is written
#: out rather than derived from the first letter: every name here is read as
#: letters, so all of them take "an" where the spelling suggests "a".
_HTML = (
    "an HTML",
    "CSS that draws nothing, off-screen positioning and text the page never paints",
)
_CONTAINERS = {
    "html": _HTML,
    "head": _HTML,
    "body": _HTML,
    "svg": ("an SVG", "zero opacity, zero size and elements the drawing never renders"),
}


def _container(text: str) -> tuple[str, str]:
    """What this text is a document *of*, where that is not plain text.

    Returns the format's name and what this tool does not read in it, or two
    empty strings where the file is what it looks like.
    """
    stripped = text.lstrip("﻿ \t\r\n")
    if stripped.startswith("{\\rtf"):
        return "an RTF", "runs marked hidden with the \\v control word"

    rest = stripped
    while True:
        skipped = _PREAMBLE.match(rest)
        if not skipped or not skipped.end():
            break
        rest = rest[skipped.end() :]

    doctype = _DOCTYPE.match(rest)
    if doctype:
        named = _CONTAINERS.get(doctype.group(1).lower())
        if named:
            return named
        rest = rest[doctype.end() :]
        while True:
            skipped = _PREAMBLE.match(rest)
            if not skipped or not skipped.end():
                break
            rest = rest[skipped.end() :]

    root = _ROOT.match(rest)
    if root:
        named = _CONTAINERS.get(root.group(1).lower())
        if named:
            return named
    return "", ""


def read_plain(path: Path) -> Extraction:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise UnreadableFile(f"cannot read {path}: {exc}") from exc

    if b"\x00" in raw:
        raise UnreadableFile(
            f"{path.name} contains null bytes and is not text; "
            "unmasker reads PDF, DOCX, ODT, XLSX, ODS and text files"
        )

    try:
        # Deliberately not `utf-8-sig`. A byte-order mark is a character this
        # tool has an opinion about: leading is how the file was saved, and
        # anywhere else is a finding. Stripping it here would throw the
        # evidence away before the detector ever saw it.
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UnreadableFile(
            f"{path.name} is not valid UTF-8 ({exc.reason} at byte {exc.start})"
        ) from exc

    remarks: list[str] = []
    unsearched: list[str] = []

    if not text.strip():
        remarks.append(
            "the file holds no text, so there was nothing to search"
            if not text
            else "the file holds only whitespace, so there was nothing to search"
        )

    name, mechanisms = _container(text)
    if name:
        bare = name.split()[-1]
        remarks.append(
            f"this is {name} document. Its text was read and searched for hidden "
            f"characters, but {bare} hides text in ways nothing here reads - "
            f"{mechanisms} - so those were not looked for"
        )
        unsearched.append(f"the ways {bare} hides text")

    return Extraction(
        kind="plain",
        units=(TextUnit(text=text),),
        remarks=tuple(remarks),
        unsearched=tuple(unsearched),
    )
