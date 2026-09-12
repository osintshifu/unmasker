#!/usr/bin/env python3
"""Build the workbook whose cell holds a number and shows nothing.

A spreadsheet separates what a cell *is* from what it *looks like*, and the
oldest way to hide a figure is to give it a format that draws nothing at all.
The cell is not hidden, its row is not hidden, its column is not hidden. It is
empty to look at and holds 250,000 to anything that reads the file.

The two families fail at this differently, which is why the pair is here:

    .xlsx   the value is read and reported as text on the sheet
    .ods    the value is dropped, and nothing says it was ever there

Neither is the right answer, and they are wrong in opposite directions - one
claims a figure is visible, the other loses it. Both are the same mistake
underneath: what a cell stores and what it draws are two different things, and
a reader that takes one for the other has answered a question nobody asked.

The chain is different in each, too. A `.xlsx` states the cell's style number,
which indexes `cellXfs`, which names a `numFmtId`, which is defined in
`numFmts` - and LibreOffice writes the format as `""`, an empty literal, where
the folklore of this trick is `;;;`. A `.ods` states the value and the drawn
text on the cell itself, `office:value="250000"` beside an empty `<text:p/>`,
so no style has to be resolved at all.

The second cell in each row is a control: an ordinary number in an ordinary
format, which must go on being read as something a person can see.

Everything in the text and the numbers is invented.

Usage:

    python3 tests/specimens/sources/build_undrawn_cell.py tests/specimens
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

FODS = """<?xml version="1.0" encoding="UTF-8"?>
<office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
 xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
 xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 office:version="1.3" office:mimetype="application/vnd.oasis.opendocument.spreadsheet">
 <office:meta><dc:creator>Marek Zapasowy-Przyklad</dc:creator></office:meta>
 <office:automatic-styles>
  <number:number-style style:name="N100"><number:text/></number:number-style>
  <style:style style:name="ce1" style:family="table-cell" style:data-style-name="N100"/>
 </office:automatic-styles>
 <office:body><office:spreadsheet>
  <table:table table:name="Scores">
   <table:table-row>
    <table:table-cell office:value-type="string"><text:p>Reserve price</text:p></table:table-cell>
    <table:table-cell table:style-name="ce1" office:value-type="float"
     office:value="250000"><text:p/></table:table-cell>
   </table:table-row>
   <table:table-row>
    <table:table-cell office:value-type="string"><text:p>Bids received</text:p></table:table-cell>
    <table:table-cell office:value-type="float" office:value="4"
     ><text:p>4</text:p></table:table-cell>
   </table:table-row>
  </table:table>
 </office:spreadsheet></office:body>
</office:document>
"""


def main(out: Path) -> None:
    work = Path(tempfile.mkdtemp(prefix="unmasker-undrawn-"))
    source = work / "scores.fods"
    source.write_text(FODS, encoding="utf-8")

    for extension in ("xlsx", "ods"):
        subprocess.run(
            [
                "soffice", "--headless", "--norestore",
                f"-env:UserInstallation=file://{work / 'loprofile'}",
                "--convert-to", extension, "--outdir", str(work), str(source),
            ],
            check=True, capture_output=True, timeout=300,
        )
        data = (work / f"scores.{extension}").read_bytes()
        if data[:4] != b"PK\x03\x04":
            raise RuntimeError(f"LibreOffice did not write a zip for {extension}")
        target = out / extension / f"libreoffice-calc-undrawn-cell.{extension}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        print(f"{target}  {len(data)} bytes")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "tests/specimens"))
