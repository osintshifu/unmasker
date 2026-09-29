<div align="center">

# unmasker

### What a human sees in a document, against what a machine reads out of it.

**Local, read-only detection of hidden, residual and failed-redaction content in documents.**

[![PyPI](https://img.shields.io/pypi/v/unmasker?style=flat-square&color=3775A9)](https://pypi.org/project/unmasker/)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?style=flat-square)
![27 detectors](https://img.shields.io/badge/detectors-27-8250df?style=flat-square)
![Runtime dependencies](https://img.shields.io/badge/runtime_dependencies-1-1f883d?style=flat-square)
![Local and read-only](https://img.shields.io/badge/local_%26_read--only-yes-1f883d?style=flat-square)
![Network requests](https://img.shields.io/badge/network_requests-none-1f883d?style=flat-square)
[![CI](https://github.com/osintshifu/unmasker/actions/workflows/ci.yml/badge.svg)](https://github.com/osintshifu/unmasker/actions/workflows/ci.yml)
![License](https://img.shields.io/badge/license-Apache--2.0-8250df?style=flat-square)

[Install](#installation) ·
[Usage](#usage) ·
[What it finds](#what-it-finds) ·
[Examples](#practical-examples) ·
[Detector reference](#detector-reference) ·
[Automation](#json-and-automation)

</div>

---

unmasker finds content that survives inside a document but is hidden, covered,
deleted, filtered, cropped or otherwise absent from what a person normally
sees.

A black rectangle drawn over text is not a redaction. The page may look clean
while the original text remains in the file and is still readable by a parser.
unmasker reports that mismatch and stops there - evidence, not a verdict.

```bash
unmasker tests/specimens/pdf/libreoffice-writer-black-bars.pdf
```

```text
  unmasker                                                      4 findings
    tests/specimens/pdf/libreoffice-writer-black-bars.pdf
  ────────────────────────────────────────────────────────────────────────

  ● 22 characters under a black shape at x 117.5-268.7, y           page 1
    684.2-698.5; the rest of the line still reads "Name:"
  │ human sees     ██████████████████████
  │ machine reads  Wanda Testowa-Przyklad

  ● 21 characters under a black shape at x 114.8-259.3, y           page 1
    664.5-678.7; the rest of the line still reads "Email:"
  │ human sees     █████████████████████
  │ machine reads  w.testowa@example.org

  ● 15 characters under a black shape at x 123.1-228.1, y           page 1
    644.7-658.9; the rest of the line still reads "Telephone:"
  │ human sees     ███████████████
  │ machine reads  +48 601 000 000

  ● 37 characters under a black shape at x 119.0-369.1, y           page 1
    624.9-639.2; the rest of the line still reads "Address:"
  │ human sees     █████████████████████████████████████
  │ machine reads  ul. Przykladowa 12/3, 00-001 Warszawa

  notes                                                             1 note
  ────────────────────────────────────────────────────────────────────────
    the file says it was made by Creator Writer; Producer LibreOffice
    24.2, and dates itself CreationDate 2026-08-31T20:25:50Z

  ────────────────────────────────────────────────────────────────────────
  searched 1 page of 1. 4 findings in 1 kind.
  sha256 fbaeef0d794f2bdb6f4c6bb823686a10d1e1b67e6b2d49df5fe33fd9a281f1a5
```

Every finding says what a human sees, what a machine reads, where the mismatch
is and how the tool knows.

Every example on this page runs against a file in the repository, so the
output below each command is what that command prints.

## Installation

```bash
pipx install unmasker
```

Or:

```bash
uv tool install unmasker
```

Python 3.10 or later. The default install has one runtime dependency: `pypdf`.
unmasker runs locally, makes no network requests and never modifies the file it
is given. Two optional flags call other programs — `--ocr` needs ghostscript and
tesseract, `--render` needs LibreOffice — and both are off unless asked for.

From a checkout:

```bash
git clone https://github.com/osintshifu/unmasker
cd unmasker
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/unmasker document.pdf
```

## Usage

```text
unmasker <file>   [options]
unmasker <folder> [options]
```

Scan one file:

```bash
unmasker document.pdf
```

Survey a folder:

```bash
unmasker ~/cases/kowalski
```

Produce machine-readable or shareable output:

```bash
unmasker document.pdf --json
unmasker document.pdf --md > report.md
unmasker ~/cases/kowalski --html > report.html
```

| Option | Purpose |
| :--- | :--- |
| `--json` | one JSON object, for a script to sort or filter |
| `--html` | one self-contained HTML report, ready to send to someone |
| `--md` | Markdown for a wiki, a ticket or a pull request |
| `--ocr` | render a page and read it back to catch mismatches without knowing the hiding technique |
| `--render` | lay a word-processor document out with LibreOffice and look at what it paints; one file at a time, refused on a folder |
| `--width N` | wrap terminal output at N columns |
| `--version` | print the version and exit |
| `-h`, `--help` | show the full option list |

Exit status is part of the interface:

| Code | Meaning |
| :--- | :--- |
| `0` | the analysis finished and established nothing |
| `1` | one or more findings were established |
| `2` | nothing was established and the analysis did not finish |

> **A file the tool did not finish reading is not a file that came back
> clean.** unmasker keeps those states separate so a pipeline cannot silently
> treat an unfinished analysis as a clean result.

A finding outranks an unfinished analysis. `1` never weakens to `2`: an OCR
pass that failed on page 7 does not make the black bar on page 1 less real,
and `2` is the code a pipeline is most likely to treat as its own problem and
retry. Both facts are in the report and in `--json`, where the `complete`
field carries the second one.

## What it finds

| Area | Examples |
| :--- | :--- |
| PDF pages | covered text, text under images, invisible text, low contrast, off-page content |
| PDF revisions | pages and text left in the file by an incremental update, which the current document no longer points at |
| Unicode | zero-width characters, bidi controls, tag characters, mixed scripts |
| Word / ODT | tracked deletions, comments, revision history, metadata leaks |
| Excel / Calc | hidden sheets, rows and columns, filtered rows, tracked cell changes, and a value a cell holds but draws nothing of |
| PowerPoint / Impress | hidden slides, speaker notes, a shape drawn over text, and text parked beside a slide |
| JPEG | stale EXIF thumbnails that can preserve content removed by cropping, and the XMP edit history an editor left behind |
| Metadata | undisclosed values, local filesystem paths and conflicting metadata copies |
| Legacy Word | a `.doc`'s text, story by story — body, footnotes, headers, footers, text boxes — with its comments, tracked changes and hidden runs |
| Legacy Office | what a `.xls` or `.ppt` says about itself, out of its compound-file property streams |
| Attachments | whole files carried inside a document, which no page mentions — and what a carried workbook hides in turn |
| OCR comparison | text present in the file but absent from the rendered page, and the reverse |

Supported inputs are PDF, DOCX, ODT, XLSX, ODS, PPTX, ODP, JPEG, UTF-8 text and legacy `.doc`, plus `.xls` and `.ppt` for their metadata.
Content is identified from the file itself rather than trusted solely from the
extension.

### What runs on what

Not every check runs on every format, and a check that did not run cannot
report anything. **If a format is missing from a row, that question was never
asked about your file** — which is not the same answer as asking it and
finding nothing.

| What is checked | Runs on |
| :--- | :--- |
| a filled shape or an image drawn over text | PDF, PPTX, ODP |
| text placed where the page or the slide does not show it | PDF, PPTX, ODP |
| faint text, and text the page does not paint at all | PDF |
| characters in the text: zero-width, direction controls, tag characters, mixed scripts | PDF, DOCX, ODT, XLSX, ODS, PPTX, ODP, DOC, text |
| text or a value the file says not to draw | DOCX, ODT, DOC, XLSX, ODS |
| hidden sheets, rows and columns, and filtered rows | XLSX, ODS |
| hidden slides and speaker notes | PPTX, ODP |
| the embedded thumbnail against the image it sits in | JPEG |
| tracked changes and comments | DOCX, ODT, DOC, XLSX, ODS |
| whole files carried inside the document | PDF, DOCX, ODT, XLSX, ODS, PPTX, ODP |
| earlier revisions the file still holds | PDF |
| metadata against the document's own text | PDF, DOCX, ODT, XLSX, ODS, PPTX, ODP, DOC, XLS, PPT, JPEG |

`--render` adds DOCX and ODT to the first row, by laying the document out with
LibreOffice and looking at what it paints. It answers about that rendering
rather than about the file, so what it finds is circumstantial and says so.

## Practical examples

### Text under an image

```bash
unmasker tests/specimens/pdf/libreoffice-writer-image-over-text.pdf
```

```text
  unmasker                                                       1 finding
    tests/specimens/pdf/libreoffice-writer-image-over-text.pdf
  ────────────────────────────────────────────────────────────────────────

  ● 22 characters under an image at x 123.3-245.9, y 702.8-720.0;   page 1
    an image over a text layer is also what a scan of a printed
    page looks like, and there the two normally agree; the rest of
    the line still reads "Subject:"
  │ human sees     ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒
  │ machine reads  Ludmila Wieczorek-Test

  notes                                                             1 note
  ────────────────────────────────────────────────────────────────────────
    the file says it was made by Creator Writer; Producer LibreOffice
    24.2, and dates itself CreationDate 2026-08-31T23:50:46Z

  ────────────────────────────────────────────────────────────────────────
  searched 1 page of 1. 1 finding in 1 kind.
  sha256 d324105840b72c0d76c491150fe9220eabb4a87a3735afdb5de5af4c27fa0b66
```

An image over text is also what a scan of a printed page looks like.
unmasker says so in the finding rather than calling it a redaction.

### Hidden spreadsheet data

```bash
unmasker tests/specimens/xlsx/libreoffice-calc-hidden-columns.xlsx
```

```text
  unmasker                                                      7 findings
    tests/specimens/xlsx/libreoffice-calc-hidden-columns.xlsx
  ────────────────────────────────────────────────────────────────────────

  comment                                                        1 finding
  ────────────────────────────────────────────────────────────────────────
  ● a comment by Halina Probna-Test, at a time the file does    whole file
    not state, carried in the file and not part of the
    document body
  │ human sees     nothing on the page
  │ machine reads  Panel agreed the reserve before the bids were opened.
  │                Not for the file we release.

  revision-history                                               1 finding
  ────────────────────────────────────────────────────────────────────────
  ● the file records 1 comment, by 1 person. A name here is     whole file
    whatever the application that wrote it was configured to
    say
  │ human sees     nothing on the page
  │ machine reads  Halina Probna-Test

  hidden-sheet                                                   1 finding
  ────────────────────────────────────────────────────────────────────────
  ● sheet "Workings" is marked hidden, and holds 1 value still  whole file
    in the file
  │ human sees     nothing on the page
  │ machine reads  Reserve set at 240,000. Kowalski came in 12% under; the
  │                others were told nothing.

  hidden-rows                                                    1 finding
  ────────────────────────────────────────────────────────────────────────
  ● row 4 of sheet "Evaluation" is hidden, and holds 6 values   whole file
    still in the file
  │ human sees     nothing on the page
  │ machine reads  Delta Consulting sp. z o.o. | 82 | 44 | 196000 | 63 |
  │                withdrawn after the deadline - do not list

  hidden-columns                                                 1 finding
  ────────────────────────────────────────────────────────────────────────
  ● column D of sheet "Evaluation" is hidden, and holds 5       whole file
    values still in the file
  │ human sees     nothing on the page
  │ machine reads  Reserve price (EUR) | 211000 | 238000 | 196000 | 251000

  undisclosed-metadata                                          2 findings
  ────────────────────────────────────────────────────────────────────────
  ● the creator field of docProps/core.xml holds a value the    whole file
    document does not show anywhere in its text
  │ human sees     nothing on the page
  │ machine reads  Halina Probna-Test

  ● the title field of docProps/core.xml holds a value the      whole file
    document does not show anywhere in its text
  │ human sees     nothing on the page
  │ machine reads  Tender evaluation - panel copy

  notes                                                             1 note
  ────────────────────────────────────────────────────────────────────────
    the file says it was made by Application
    LibreOffice/24.2.7.2$Linux_X86_64 LibreOffice_project/420$Build-2;
    AppVersion 15.0000, and counts revision 0; TotalTime 0

  ────────────────────────────────────────────────────────────────────────
  searched the text of this file. 7 findings in 6 kinds.
  sha256 6cb60d45c5e8fe7b2c05c1eee565ec417079909800f48209c88b28c42ec53c8e
```

### Case-folder triage

```bash
unmasker tests/specimens/docx
```

```text
  unmasker  tests/specimens/docx                             6 of 12 files
  ────────────────────────────────────────────────────────────────────────
    read      12 files, 20 findings
    not read  0 files

  what was found                                                  12 kinds
  ────────────────────────────────────────────────────────────────────────
    undisclosed-metadata  3 files
    attached-file         1 file
    hidden-sheet          1 file
    zero-width            1 file
    bidi-control          1 file
    tag-characters        1 file
    mixed-script          1 file
    invisible-text        1 file
    metadata-path         1 file
    deleted-text          1 file
    comment               1 file
    revision-history      1 file

  files that hide something                                        6 files
  ────────────────────────────────────────────────────────────────────────
    libreoffice-writer-covered-text.docx       undisclosed-metadata
    libreoffice-writer-embedded-sheet.docx     attached-file, hidden-sheet
    libreoffice-writer-hidden-characters.docx  zero-width, bidi-control,
                                               tag-characters,
                                               mixed-script
    libreoffice-writer-hidden-run.docx         invisible-text,
                                               undisclosed-metadata
    libreoffice-writer-metadata-leak.docx      undisclosed-metadata,
                                               metadata-path
    libreoffice-writer-tracked-changes.docx    deleted-text, comment,
                                               revision-history

  ────────────────────────────────────────────────────────────────────────
  searched 12 files. unmasker <file> for the detail, --json for all of it.
```

A directory scan reports what was read, what could not be read, which detector
kinds appeared and which files contain findings. It does not rank files by
"severity". Use the detailed file report or `--json` for every finding.

### Read the rendered page back

```bash
unmasker scan.pdf --ocr
```

`--ocr` asks a different question: does the text stored in the document agree
with the page after it is rendered? This can expose a hiding technique for
which there is no dedicated detector yet.

For PDF page comparison it requires `ghostscript` and `tesseract` on `PATH` and
costs seconds per page, so it is opt-in and refused for directory surveys.

## Detector reference

The detector slug is stable output intended for reports and automation.

### Page and rendering

| Detector | What it reports |
| :--- | :--- |
| `covered-text` | text underneath a filled shape — per character in a PDF, per text box on a slide |
| `text-under-image` | text underneath an image, kept distinct from a filled-shape redaction |
| `invisible-text` | text the file tells the application not to draw — a PDF render mode that paints nothing, or a Word run marked hidden |
| `low-contrast-text` | text too close in colour to the background behind it |
| `off-page-text` | text outside the visible page or crop box, and text parked beside a slide rather than on it |
| `unrendered-text` | words stored in the file that OCR cannot find on the rendered page |
| `unextractable-text` | words visible to OCR on the rendered page but absent from the extracted text |

### Characters

| Detector | What it reports |
| :--- | :--- |
| `zero-width` | zero-width spaces, joiners, soft hyphens and word joiners |
| `bidi-control` | Unicode direction controls that can change how a string appears on screen |
| `tag-characters` | plane-14 Unicode tag characters, decoded when possible |
| `mixed-script` | a single word containing characters from multiple scripts |

### Spreadsheets

| Detector | What it reports |
| :--- | :--- |
| `hidden-sheet` | a hidden or very-hidden sheet that still carries values |
| `hidden-rows` | hidden rows that still carry values, collapsed into blocks |
| `hidden-columns` | hidden columns that still carry values |
| `filtered-rows` | rows currently excluded by a worksheet filter |
| `changed-cell` | a tracked cell change, including the replaced value when available |

### Presentations

| Detector | What it reports |
| :--- | :--- |
| `hidden-slide` | a slide stored in the deck but skipped when the presentation is shown |
| `speaker-notes` | speaker-note text that never appears on the projected slide |

### Images

| Detector | What it reports |
| :--- | :--- |
| `stale-thumbnail` | an embedded EXIF preview whose dimensions show it was not regenerated from the current image |

### Container, revisions and metadata

| Detector | What it reports |
| :--- | :--- |
| `deleted-text` | text preserved inside a tracked deletion |
| `comment` | comments and annotations stored with the document |
| `revision-history` | document revision authorship and edit history |
| `undisclosed-metadata` | metadata values that do not appear in the document's visible text |
| `metadata-path` | filesystem paths exposed by document metadata |
| `metadata-conflict` | contradictory copies of metadata stored inside the same file |
| `attached-file` | a whole file carried inside the document, on no page and not printed with it |
| `earlier-revision` | text an earlier revision of the file still holds, which no page shows now |

## Evidence model

unmasker reports observable mismatches. It does not decide whether a document
is malicious, manipulated or safe.

Each finding carries one of three evidence bases:

- **direct** - the relevant bytes are in the file and were read out directly
- **circumstantial** - the observation is consistent with hiding, but an innocent explanation can also fit
- **self-reported** - the document or application reports the fact about itself

There are no severity scores and no ranking. Findings are not ordered by how
bad they are, because that is the reader's judgement to make.

> **"Nothing found" and "nothing could be searched" are different results.**
> unmasker keeps them separate. JSON exposes this explicitly through the
> `searched` field.

Values are not shortened with ellipses. If evidence is long, the report wraps
it instead of silently dropping part of it.

## Reports

The terminal report is for triage. Three stdout formats are available when the
result needs to be stored, processed or sent to someone else:

- `--json` for automation
- `--html` for a self-contained human-readable report
- `--md` for Markdown-based systems

unmasker treats report content as untrusted because every quoted value came
from a file being investigated. HTML values are escaped, Markdown evidence is
fenced or escaped, and generated HTML contains no JavaScript or external
resources.

There is no `--out` option: redirect the output where you want it.

## JSON and automation

`--json` writes one object on stdout while the exit status remains usable as a
pipeline gate:

```bash
unmasker document.pdf --json > findings.json
case $? in
  0) echo "clean" ;;
  1) echo "findings exist" ;;
  2) echo "analysis did not finish - see remarks in findings.json" ;;
esac
```

The JSON shape is versioned separately from the package version:

| Field | Meaning |
| :--- | :--- |
| `schema` | `unmasker.scan/1` for one file or `unmasker.survey/1` for a folder |
| `version` | the unmasker build that produced the report |
| `searched` | `false` means there was nothing to search, not that a search came back empty |
| `complete` | `false` means a check this tool makes was not made: a container it recognised and does not read, a part that would not parse, or an `--ocr` or `--render` step that failed |
| `sha256` | the digest of the bytes that were read, so a finding can be checked against the file rather than the path |
| `location.inside` | present when a finding came out of a file the document carries, naming it |

```bash
unmasker tests/specimens/pdf/libreoffice-writer-image-over-text.pdf --json
```

```json
{
  "tool": "unmasker",
  "schema": "unmasker.scan/1",
  "version": "0.7.0",
  "file": "tests/specimens/pdf/libreoffice-writer-image-over-text.pdf",
  "sha256": "d324105840b72c0d76c491150fe9220eabb4a87a3735afdb5de5af4c27fa0b66",
  "kind": "pdf",
  "searched": true,
  "complete": true,
  "remarks": [
    "the file says it was made by Creator Writer; Producer LibreOffice 24.2, and dates itself CreationDate 2026-08-31T23:50:46Z"
  ],
  "findings": [
    {
      "detector": "text-under-image",
      "basis": "direct",
      "summary": "22 characters under an image at x 123.3-245.9, y 702.8-720.0; an image over a text layer is also what a scan of a printed page looks like, and there the two normally agree; the rest of the line still reads \"Subject:\"",
      "human_sees": "▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒",
      "machine_reads": "Ludmila Wieczorek-Test",
      "location": {
        "page": 1
      },
      "codepoints": [
        "U+004C",
        "U+0075",
        "U+0064",
        "U+006D",
        "U+0069",
        "U+006C",
        "U+0061",
        "U+0020",
        "U+0057",
        "U+0069",
        "U+0065",
        "U+0063",
        "U+007A",
        "U+006F",
        "U+0072",
        "U+0065",
        "U+006B",
        "U+002D",
        "U+0054",
        "U+0065",
        "U+0073",
        "U+0074"
      ]
    }
  ]
}
```

The `/1` changes only when the JSON shape changes incompatibly. A normal
package release does not force downstream consumers to guess whether their
parser still works.

## What unmasker is not

unmasker is not a malware scanner, DLP system, authenticity classifier or
forensic verdict engine. It exposes discrepancies and residual content so a
human or a downstream system can decide what they mean.

## Limits

- No verdicts about whether a document was manipulated or malicious.
- No writing to the input file and no network access.
- What a page paints is read straight from the file for PDF, and computed from the file for `.pptx` and `.odp`, where every shape carries absolute coordinates against a known slide size.
- A word processor states neither. Its text flows, so a `.docx` or `.odt` says there is a filled shape and says there is text and never says one is over the other. `--render` answers it by laying the document out with LibreOffice and looking at what got painted — which means handing the file to another program, and answering about that rendering rather than about the file. Word lays a page out differently, so a bar that covers a name there may miss it here. Every finding from it is circumstantial and names the rendering it came from.
- A `.doc` is read for its text as well as its metadata, including its footnotes, headers, comments, tracked changes and hidden text. Objects embedded in it are not opened, and character formatting other than the hidden attribute is not read.
- `.xls` and `.ppt` are read for what they say about themselves, not for their text. The compound-file container and both property streams are read; the BIFF and PowerPoint record streams inside them are not.
- Signature coverage is not checked. A signed PDF's `/ByteRange` says which bytes the signature covers, and unmasker does not compare it against the rest of the file.
- XMP is read in PDF and JPEG. DOCX and TIFF carry packets too and are not read yet.
- Different applications encode the same feature differently, and coverage is strongest against files written by LibreOffice and the other open-source producers. A document written by Microsoft Word or Adobe Acrobat may store something in a way unmasker does not yet recognise.
- OCR is optional, slower than structural detection and depends on external tools.

## License

Apache License 2.0.

---

<div align="center">

**unmasker**

*What a human sees in a document, against what a machine reads out of it.*

Made by [osintshifu](https://github.com/osintshifu)

</div>
