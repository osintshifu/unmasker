"""A cell that holds a number and shows nothing.

A spreadsheet separates what a cell *is* from what it *looks like*, and the
oldest way to hide a figure is a format that draws nothing at all. The cell is
not hidden, its row is not hidden, its column is not hidden. It is empty to
look at and holds 250,000 to anything that reads the file.

The two families were wrong about it in opposite directions: `.xlsx` read the
value and reported it as text on the sheet, `.ods` dropped it and said nothing
had been found. One claims a figure is visible, the other loses it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from unmasker.detect import collect
from unmasker.readers import read

SPECIMENS = Path(__file__).parent / "specimens"
PAIR = (
    SPECIMENS / "xlsx" / "libreoffice-calc-undrawn-cell.xlsx",
    SPECIMENS / "ods" / "libreoffice-calc-undrawn-cell.ods",
)


@pytest.mark.parametrize("path", PAIR, ids=lambda p: p.suffix.lstrip("."))
def test_a_value_the_sheet_draws_nothing_for_is_reported(path):
    found = [f for f in collect(read(path)) if f.detector == "invisible-text"]
    assert len(found) == 1
    assert "250000" in found[0].machine_reads


@pytest.mark.parametrize("path", PAIR, ids=lambda p: p.suffix.lstrip("."))
def test_it_does_not_count_as_a_figure_on_the_sheet(path):
    shown = "\n".join(unit.text for unit in read(path).units)
    assert "250000" not in shown
    assert "Reserve price" in shown


@pytest.mark.parametrize("path", PAIR, ids=lambda p: p.suffix.lstrip("."))
def test_an_ordinary_number_is_still_read_as_something_a_person_sees(path):
    """The control. A format rule that swallowed real figures would be worse
    than the gap it was written to close."""
    shown = "\n".join(unit.text for unit in read(path).units)
    assert "4" in shown
    assert not [
        f
        for f in collect(read(path))
        if f.detector == "invisible-text" and f.machine_reads.strip() == "4"
    ]
