"""`README.md` is held against the detectors, so it cannot quietly go stale.

`about.py` argues that a count belongs "in the README beside the list it
counts", and that reasoning was right. It was also not enough: the README then
said **22 detectors** while the source emitted 25. Putting a number next to a
list does not keep the number true. Only something that fails when they
disagree does.

The count of tests is no longer stated at all. A number that grows with every
commit is a maintenance cost on the front page and tells a reader nothing they
can act on, whether or not a test keeps it honest.

So the tables are parsed. Every slug the source can emit has to appear in a
detector table, every slug in a table has to be one the source actually emits,
and the badge has to agree with both. Any of the three failing is a red test
rather than a wrong front door.

The specimen count is held the same way, at the bottom of this file.

## What counts as a detector, to a parser

A slug reaches a report in one of two ways, and both are a parameter named
`detector`: as `Finding(detector="zero-width", ...)` written out, or handed to
a helper that builds a family of them - `_under(page, ("fill",),
"covered-text")` in `pdf/detectors.py`, `_axis(record, "hidden-rows", ...)` in
`sheets.py`. Reading only the keyword form finds 20 of the 25 and calls the
document complete, which is the same shape of green-and-wrong the specimens
exist to prevent.

So this resolves the parameter by name in either position. A helper that grows
a `detector` argument is picked up with no change here; one that names the
parameter something else is not, and that is the known edge - it is why the
count is asserted as well as the set, because a slug that goes missing from
both sides at once still moves the total.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
SOURCE = ROOT / "src" / "unmasker"

#: The header row that marks a detector table. Anything else in the file is
#: prose or another kind of table and is left alone. Named columns rather than
#: `| | |`, which renders an empty header row on GitHub and gives a parser
#: nothing to key on.
DETECTOR_HEADER = ("detector", "what it reports")

#: `![... 25 detectors ...](...detectors-25-...)` in the badge line.
_BADGE = re.compile(r"badge/detectors-(\d+)-")

#: "There are 31 of them and they are the test suite".
_SPECIMENS = re.compile(r"There are (\d+) of them")

SPECIMENS = ROOT / "tests" / "specimens"

#: The first cell of a detector row is the slug and nothing else. The
#: trailing hyphens are optional: `comment` is a detector and an earlier
#: version of this pattern required one, so it read 24 of the 25 and
#: blamed the README for the one it could not see.
_SLUG = re.compile(r"^`([a-z][a-z0-9]*(?:-[a-z0-9]+)*)`$")


def _rows(header: tuple[str, ...]) -> list[tuple[str, ...]]:
    """Every row under every table whose header row matches."""
    found: list[tuple[str, ...]] = []
    inside = False
    for line in README.read_text(encoding="utf-8").splitlines():
        if not line.lstrip().startswith("|"):
            inside = False
            continue
        cells = tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
        if tuple(cell.lower() for cell in cells) == header:
            inside = True
            continue
        if inside and set("".join(cells)) <= set(":- "):
            continue  # the separator under the header
        if inside:
            found.append(cells)
    return found


def _documented() -> set[str]:
    """Every detector slug the README's tables name."""
    out = set()
    for row in _rows(DETECTOR_HEADER):
        match = _SLUG.match(row[0])
        if match:
            out.add(match.group(1))
    return out


def _emitted() -> set[str]:
    """Every slug the source can put in a `Finding`.

    Resolved through the parameter name rather than the call shape, so the
    helpers in `pdf/detectors.py` and `sheets.py` are read the same way as a
    `Finding` built in place.
    """
    found: set[str] = set()
    for path in sorted(SOURCE.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))

        # Which argument position each function in this module calls `detector`.
        position: dict[str, int] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                arguments = node.args.posonlyargs + node.args.args
                for index, argument in enumerate(arguments):
                    if argument.arg == "detector":
                        position[node.name] = index

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for keyword in node.keywords:
                if keyword.arg == "detector" and isinstance(keyword.value, ast.Constant):
                    if isinstance(keyword.value.value, str):
                        found.add(keyword.value.value)
            name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            index = position.get(name)
            if index is not None and index < len(node.args):
                argument = node.args[index]
                if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                    found.add(argument.value)
    return found


# --- the tables are there at all ---------------------------------------------


def test_the_detector_tables_are_found():
    """A header nobody can parse would make every check below vacuous."""
    assert _rows(DETECTOR_HEADER), f"no table headed {DETECTOR_HEADER} in {README.name}"


def test_the_source_emits_detectors_at_all():
    """The same guard from the other side: an extractor that silently returns
    nothing would agree with an empty README forever."""
    assert _emitted(), "no detector slugs found in the source at all"


# --- and they say what the code does -----------------------------------------


def test_every_detector_the_source_emits_is_documented():
    missing = _emitted() - _documented()

    assert not missing, f"emitted but undocumented: {sorted(missing)}"


def test_nothing_is_documented_that_the_source_never_emits():
    """A promise the tool does not keep is worse than a gap in the table."""
    invented = _documented() - _emitted()

    assert not invented, f"documented but never emitted: {sorted(invented)}"


def test_the_badge_counts_what_the_tables_list():
    """The claim on the front door, against the list behind it.

    This is the one that actually drifted: the tables were right and the badge
    said 22.
    """
    claimed = _BADGE.search(README.read_text(encoding="utf-8"))

    assert claimed, "no detector-count badge found in README.md"
    assert int(claimed.group(1)) == len(_documented()) == len(_emitted())


# --- the other two numbers on the same page ----------------------------------


def _specimen_files() -> set[Path]:
    """The committed specimens themselves.

    Not the `.md` beside each one, which is its provenance note rather than a
    specimen, and not `sources/`, which holds the builders that drive the real
    producers.
    """
    return {
        path
        for path in SPECIMENS.rglob("*")
        if path.is_file()
        and path.suffix != ".md"
        and "sources" not in path.relative_to(SPECIMENS).parts
    }


def test_the_specimen_count_is_the_number_of_specimens():
    claimed = _SPECIMENS.search(README.read_text(encoding="utf-8"))

    assert claimed, "README no longer states how many specimens there are"
    assert int(claimed.group(1)) == len(_specimen_files())


def test_every_specimen_says_where_it_came_from():
    """The README says each specimen has a provenance note. It has to be true.

    A specimen without one is a file whose producer, visible content and stored
    content are known to whoever added it and to nobody else - which makes it a
    fixture, and fixtures are what this corpus exists instead of.
    """
    missing = sorted(
        str(path.relative_to(SPECIMENS))
        for path in _specimen_files()
        if not path.with_suffix(".md").exists()
    )
    assert not missing, f"specimens with no provenance note: {missing}"


# --------------------------------------------------------------------------
# what runs on what
# --------------------------------------------------------------------------
#
# A check that did not run cannot report anything, and the README now says
# which formats reach which check. That claim went unstated for a long time,
# and while it did, `covered-text` - the finding on the front page, the one
# the wordmark is about - worked on PDF and nothing else, with nothing on the
# page saying so.
#
# The claim is derived from the readers rather than declared twice: a reader
# can only reach a detector by filling the channel that detector is gated on
# in `detect.py`.

READERS = SOURCE / "readers"

#: Which channel each row of the README table is fed by.
ROWS = {
    "what the page paints": "drawn",
    "characters in the text": "units",
    "text the file marks as not to be drawn": "hidden",
    "hidden sheets, rows and columns": "sheets",
    "hidden slides and speaker notes": "slides",
    "the embedded thumbnail": "image",
    "tracked changes and comments": "revisions",
    "whole files carried inside": "attachments",
    "earlier revisions": "earlier",
    "metadata against": "metadata",
}

#: What a reader module is called on the front page.
FORMATS = {
    "docx": ("DOCX",),
    "image": ("JPEG",),
    "legacy": ("DOC",),
    "odf": ("ODT",),
    "pdf": ("PDF",),
    "plain": ("text",),
    "presentation": ("PPTX", "ODP"),
    "spreadsheet": ("XLSX", "ODS"),
}

#: Two places where the channel a reader fills does not settle the answer.
#:
#: `legacy` reads three formats to different depths - only a .doc has its text
#: read, while a .xls and a .ppt give up their property streams and nothing
#: else - and the channel is the same object either way.
#:
#: `attachments` is filled by `read()` for every zip after the reader has
#: returned, so no reader but the PDF one mentions it.
DEPTH = {
    ("legacy", "metadata"): ("DOC", "XLS", "PPT"),
    ("pdf", "attachments"): ("PDF", "DOCX", "ODT", "XLSX", "ODS", "PPTX", "ODP"),
}


def _filled() -> dict[str, set[str]]:
    """Which reader module fills each channel of the extraction.

    A keyword whose value is written `()` is a reader saying it never has one:
    the image reader passes `units=()`, because a photograph has no text, and
    counting it would put JPEG on the row about characters in the text.
    """
    ignored = {"kind", "remarks", "source", "text_unread", "sha256"}
    out: dict[str, set[str]] = {}
    for path in sorted(READERS.glob("*.py")):
        if path.name in ("__init__.py", "model.py"):
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call) or getattr(node.func, "id", "") != "Extraction":
                continue
            for keyword in node.keywords:
                if keyword.arg in ignored or keyword.arg is None:
                    continue
                if isinstance(keyword.value, ast.Tuple) and not keyword.value.elts:
                    continue
                out.setdefault(keyword.arg, set()).add(path.stem)
    return out


def test_the_readme_says_which_formats_reach_which_check():
    filled = _filled()
    rows = {cells[0]: cells[1] for cells in _rows(("what is checked", "runs on"))}
    assert len(rows) == len(ROWS), sorted(rows)

    for lead, channel in ROWS.items():
        stated = next((v for k, v in rows.items() if k.startswith(lead)), None)
        assert stated is not None, f"the README no longer has a row for {lead!r}"

        reached: set[str] = set()
        for module in filled.get(channel, ()):
            reached.update(DEPTH.get((module, channel), FORMATS[module]))

        named = {name.strip() for name in stated.split(",")}
        assert named == reached, (lead, sorted(named), sorted(reached))
