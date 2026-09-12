#!/usr/bin/env python3
"""Build the pair of documents whose text is partly marked not to be drawn.

Word calls it `w:vanish` and OpenDocument calls it `text:display="none"`, and
both mean what a PDF render mode that paints neither fill nor stroke means:
**these characters are in the file and not on the page.**

Neither reader looked. Both folded the hidden run into the body, so the report
said it had searched the text and found nothing hidden - about a file holding
a sentence nobody printing it would ever see. Worse than a miss: a name in a
hidden run counted as shown, so the metadata detector stayed quiet about it.

One source document in two containers, because what is worth comparing is how
the two formats say the same thing.

Everything in the metadata and the text is invented.

Usage:

    python3 tests/specimens/sources/build_hidden_runs.py tests/specimens
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
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 office:version="1.3" office:mimetype="application/vnd.oasis.opendocument.text">
 <office:meta><dc:creator>Marek Zapasowy-Przyklad</dc:creator></office:meta>
 <office:automatic-styles>
  <style:style style:name="T1" style:family="text">
   <style:text-properties text:display="none"/>
  </style:style>
 </office:automatic-styles>
 <office:body><office:text>
  <text:p>Award notice. The contract has been awarded.</text:p>
  <text:p>Panel decision <text:span style:name="x" text:style-name="T1"
   >- the reserve bidder is Wykonawca B -</text:span> is final.</text:p>
 </office:text></office:body>
</office:document>
"""


def main(out: Path) -> None:
    work = Path(tempfile.mkdtemp(prefix="unmasker-hidden-"))
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

        target = out / folder / f"libreoffice-writer-hidden-run.{extension}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        print(f"{target}  {len(data)} bytes")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "tests/specimens"))
