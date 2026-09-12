#!/usr/bin/env python3
"""Build the deck where a shape is drawn over text, in both families.

Somebody drags a black rectangle over a name before sending the deck. The
rectangle is a shape; the text is still a shape underneath it, still in the
file, and still read by anything that walks the slide.

Unlike a word processor, **a slide says exactly where everything is.** Every
shape carries absolute coordinates against a known slide size and the shapes
are painted in document order, so which one is on top of which is not a guess.
That is why this check is possible here and not in a .docx.

What a slide does *not* say is where each character sits inside its text box.
A PDF gives glyph positions, so the PDF detector can name the 22 characters
under the bar and quote the rest of the line. Here the smallest thing with a
position is the whole text box, so the three frames on this slide are built to
make the difference testable:

    covered whole    the bar contains the text box            direct
    covered partly   the bar takes the left half of the box   circumstantial
    on a banner      the fill is painted first, text on top   no finding
    not covered      no shape over it at all                  no finding

The banner is the false positive worth guarding against, and it is the reason
painting order has to be read rather than assumed. Text on a coloured band is
an ordinary slide; the shapes overlap exactly as a redaction does, and only
which was painted first tells them apart.

Everything in the text is invented.

Usage:

    python3 tests/specimens/sources/build_covered_slide.py tests/specimens
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
  <style:style style:name="bar" style:family="graphic">
   <style:graphic-properties draw:fill="solid" draw:fill-color="#000000" draw:stroke="none"/>
  </style:style>
  <style:style style:name="plain" style:family="graphic">
   <style:graphic-properties draw:fill="none" draw:stroke="none"/>
  </style:style>
 </office:automatic-styles>
 <office:body><office:presentation>
  <draw:page draw:name="Award panel">
   <draw:frame draw:style-name="plain" svg:x="2cm" svg:y="2cm" svg:width="14cm" svg:height="1.2cm">
    <draw:text-box><text:p>Panel chair: Wanda Testowa-Przyklad</text:p></draw:text-box>
   </draw:frame>
   <draw:rect draw:style-name="bar" svg:x="1.8cm" svg:y="1.8cm"
    svg:width="14.4cm" svg:height="1.6cm"/>
   <draw:frame draw:style-name="plain" svg:x="2cm" svg:y="5cm" svg:width="14cm" svg:height="1.2cm">
    <draw:text-box><text:p>Reserve price 250,000 EUR, agreed 12 April.</text:p></draw:text-box>
   </draw:frame>
   <draw:rect draw:style-name="bar" svg:x="2cm" svg:y="5cm" svg:width="7cm" svg:height="1.2cm"/>
   <draw:rect draw:style-name="bar" svg:x="2cm" svg:y="8cm" svg:width="14cm" svg:height="1.2cm"/>
   <draw:frame draw:style-name="plain" svg:x="2cm" svg:y="8cm" svg:width="14cm" svg:height="1.2cm">
    <draw:text-box><text:p>Scores are on the banner, in front of it.</text:p></draw:text-box>
   </draw:frame>
   <draw:frame draw:style-name="plain" svg:x="2cm" svg:y="11cm" svg:width="14cm" svg:height="1.2cm">
    <draw:text-box><text:p>Decision published on 30 April.</text:p></draw:text-box>
   </draw:frame>
  </draw:page>
 </office:presentation></office:body>
</office:document>
"""


def main(out: Path) -> None:
    work = Path(tempfile.mkdtemp(prefix="unmasker-covered-"))
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

        target = out / extension / f"libreoffice-impress-covered-text.{extension}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        print(f"{target}  {len(data)} bytes")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "tests/specimens"))
