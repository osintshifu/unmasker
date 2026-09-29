"""`CHANGELOG.md` is held to linking every release it describes.

Eight versions in this file once rendered as `[0.7.0]` in square brackets and
nothing else, because the entries were written and the link definitions at the
foot were not. Markdown fails silently at this: a reference with no definition
is not an error, it is literal text, and the only way to notice is to read the
rendered page and try the link.

Which is the same argument `test_documented_detectors.py` makes about the
README. Writing the two halves next to each other does not keep them together;
only something that fails when they disagree does.

The release URL is derived from the packaging metadata rather than written out
here. A literal would be a third copy of an address the project already states
twice, and the third copy is the one nobody updates.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = ROOT / "CHANGELOG.md"
MANIFEST = ROOT / "pyproject.toml"

#: `## [0.7.0] - 2026-09-12`, whose bracketed version is a Markdown reference.
_ENTRY = re.compile(r"^## \[([^\]]+)\]", re.M)

#: `[0.7.0]: https://...`, the definition that turns it into a link.
_DEFINITION = re.compile(r"^\[([^\]]+)\]: (\S+)", re.M)


def _repository() -> str:
    declared = re.search(
        r'^Repository = "(https://\S+?)"', MANIFEST.read_text(encoding="utf-8"), re.M
    )
    assert declared, "pyproject.toml no longer states a Repository URL"
    return declared.group(1).rstrip("/")


def test_every_release_described_here_links_to_that_release():
    """Both directions, because both have gone wrong.

    A described version with no definition renders as bare brackets. A
    definition with no entry is a link to a release this file never explains,
    which is the same staleness pointing the other way.
    """
    text = CHANGELOG.read_text(encoding="utf-8")
    described = _ENTRY.findall(text)
    defined = dict(_DEFINITION.findall(text))

    assert not [v for v in described if v not in defined], "described and not linked"
    assert not [v for v in defined if v not in described], "linked and not described"

    base = _repository()
    wrong = {v: url for v, url in defined.items() if url != f"{base}/releases/tag/v{v}"}
    assert not wrong, f"these point somewhere other than their own tag: {wrong}"


def test_every_release_this_file_links_to_was_actually_tagged():
    """A link to a tag nobody pushed is a 404 with a version number on it.

    Checked against the repository's own tags rather than over the network:
    the answer has to be the same on a machine with no route out, and a test
    that reaches the internet fails for reasons that are not about this file.
    """
    tags = subprocess.run(
        ["git", "tag"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    if not tags:
        pytest.skip("no tags in this checkout, so there is nothing to check against")

    linked = {f"v{version}" for version, _ in _DEFINITION.findall(CHANGELOG.read_text("utf-8"))}
    untagged = sorted(linked - set(tags))
    assert not untagged, f"linked but never tagged: {untagged}"


def test_the_version_being_shipped_has_an_entry():
    """The check that catches a release with no notes.

    A version bumped in `pyproject.toml` and not written up here ships to
    people who then have no way to learn what changed. It fails at the moment
    the version moves, which is the moment the entry should have been written.
    """
    declared = re.search(r'^version = "([^"]+)"', MANIFEST.read_text(encoding="utf-8"), re.M)
    assert declared, "pyproject.toml no longer states a version"
    assert declared.group(1) in _ENTRY.findall(CHANGELOG.read_text(encoding="utf-8"))
