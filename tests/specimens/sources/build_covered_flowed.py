#!/usr/bin/env python3
"""Build the word-processor document with a shape drawn over its text.

The same act as the slide specimen and the PDF one - a black rectangle dragged
over a figure before the file goes out - in the family where **the file does
not say whether it worked.**

A slide states absolute coordinates against a known slide size, so the overlap
is arithmetic. A word processor lays its text out as it flows: the shape has an
anchor and an offset, the text has none at all, and where the two meet is
decided by the application that opens the document. Two applications can
disagree, and the file is not the arbiter.

So this specimen is not here to be measured. It is here so that laying the
document out and looking at what got painted can be shown to find what reading
the markup cannot - and so that the finding can be seen to say which of those
two things it is.

The first offset tried put the bar over the paragraph *above* the one it is
anchored to, which is the point made against the specimen's author: the same
number means different things after a round trip, and only laying the file out
says which. The one committed here was chosen by rendering it and looking.

Everything in the text is invented.

Usage:

    python3 tests/specimens/sources/build_covered_flowed.py tests/specimens
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

FODT = """<?xml version="1.0" encoding="UTF-8"?>
<office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
 xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
 xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
 xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 office:version="1.3" office:mimetype="application/vnd.oasis.opendocument.text">
 <office:meta><dc:creator>Marek Zapasowy-Przyklad</dc:creator></office:meta>
 <office:automatic-styles>
  <style:style style:name="bar" style:family="graphic">
   <style:graphic-properties draw:fill="solid" draw:fill-color="#000000"
    draw:stroke="none" style:run-through="foreground" style:wrap="run-through"
    style:vertical-pos="from-top" style:horizontal-pos="from-left"/>
  </style:style>
 </office:automatic-styles>
 <office:body><office:text>
  <text:p>Award notice for the panel.</text:p>
  <text:p><draw:rect draw:style-name="bar" text:anchor-type="paragraph"
   svg:x="0cm" svg:y="0cm" svg:width="11cm" svg:height="0.6cm"
   />Reserve price is 250,000 EUR and must not leave the panel.</text:p>
  <text:p>Decision published on 30 April.</text:p>
 </office:text></office:body>
</office:document>
"""


def main(out: Path) -> None:
    work = Path(tempfile.mkdtemp(prefix="unmasker-flowed-"))
    source = work / "notice.fodt"
    source.write_text(FODT, encoding="utf-8")

    for extension, folder in (("docx", "docx"), ("odt", "odt")):
        subprocess.run(
            [
                "soffice", "--headless", "--norestore",
                f"-env:UserInstallation=file://{work / 'loprofile'}",
                "--infilter=OpenDocument Text Flat XML",
                "--convert-to", extension, "--outdir", str(work), str(source),
            ],
            check=True, capture_output=True, timeout=300,
        )
        data = (work / f"notice.{extension}").read_bytes()
        if data[:4] != b"PK\x03\x04":
            raise RuntimeError(f"LibreOffice did not write a zip for {extension}")
        target = out / folder / f"libreoffice-writer-covered-text.{extension}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        print(f"{target}  {len(data)} bytes")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "tests/specimens"))
