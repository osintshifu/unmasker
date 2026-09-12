#!/usr/bin/env python3
"""Build the deck with a text box parked outside the slide.

The pasteboard around a slide is working space. Text dragged onto it is gone
from the projector, gone from the print and gone from the PDF - and still in
the file, still in the shape tree, still read by anything that walks it.

Nobody has to mean anything by it. A line cut from the talk and left beside
the slide is the ordinary way that space gets used, which is exactly why the
line is still there when the deck is sent on.

Three boxes, and each pins a different part of the answer:

    on the slide       inside the slide rectangle          no finding
    parked beside it   no overlap with the slide at all    reported
    overhanging        crosses the edge, partly visible    no finding

The third is the one that decides whether this detector is usable. A title box
wider than its slide is ordinary layout, and a slide gives no glyph positions -
so an overhang cannot be told from a sentence pushed half off the edge, and
reporting it would fire on decks that hide nothing. Only a box with no overlap
at all is reported.

Everything in the text is invented.

Usage:

    python3 tests/specimens/sources/build_offstage_slide.py tests/specimens
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

FODP = """<?xml version="1.0" encoding="UTF-8"?>
<office:document xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
 xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
 xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
 xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 office:version="1.3" office:mimetype="application/vnd.oasis.opendocument.presentation">
 <office:meta><dc:creator>Marek Zapasowy-Przyklad</dc:creator></office:meta>
 <office:automatic-styles>
  <style:style style:name="plain" style:family="graphic">
   <style:graphic-properties draw:fill="none" draw:stroke="none"/>
  </style:style>
 </office:automatic-styles>
 <office:body><office:presentation>
  <draw:page draw:name="Award panel">
   <draw:frame draw:style-name="plain" svg:x="2cm" svg:y="2cm"
    svg:width="14cm" svg:height="1.2cm">
    <draw:text-box><text:p>Award notice for the panel.</text:p></draw:text-box>
   </draw:frame>
   <draw:frame draw:style-name="plain" svg:x="34cm" svg:y="2cm"
    svg:width="14cm" svg:height="1.2cm">
    <draw:text-box><text:p
     >Cut from the talk: reserve bidder is Wykonawca B.</text:p></draw:text-box>
   </draw:frame>
   <draw:frame draw:style-name="plain" svg:x="24cm" svg:y="6cm"
    svg:width="14cm" svg:height="1.2cm">
    <draw:text-box><text:p>Overhanging the right edge.</text:p></draw:text-box>
   </draw:frame>
  </draw:page>
 </office:presentation></office:body>
</office:document>
"""


def main(out: Path) -> None:
    work = Path(tempfile.mkdtemp(prefix="unmasker-offstage-"))
    source = work / "panel.fodp"
    source.write_text(FODP, encoding="utf-8")

    for extension in ("pptx", "odp"):
        subprocess.run(
            [
                "soffice", "--headless", "--norestore",
                f"-env:UserInstallation=file://{work / 'loprofile'}",
                "--infilter=OpenDocument Presentation Flat XML",
                "--convert-to", extension, "--outdir", str(work), str(source),
            ],
            check=True, capture_output=True, timeout=300,
        )
        data = (work / f"panel.{extension}").read_bytes()
        if data[:4] != b"PK\x03\x04":
            raise RuntimeError(f"LibreOffice did not write a zip for {extension}")
        target = out / extension / f"libreoffice-impress-offstage-text.{extension}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        print(f"{target}  {len(data)} bytes")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "tests/specimens"))
