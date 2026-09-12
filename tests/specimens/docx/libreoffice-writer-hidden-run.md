# `libreoffice-writer-hidden-run.docx`

**Producer:** LibreOffice 24.2 Writer. Built by
[`sources/build_hidden_runs.py`](../sources/build_hidden_runs.py), which writes
this and [`odt/libreoffice-writer-hidden-run.odt`](../odt/libreoffice-writer-hidden-run.odt)
from one source document.

## What a person sees

Two lines:

> Award notice. The contract has been awarded.
> Panel decision  is final.

## What is stored inside

Between *decision* and *is final* sits a run Word is told not to draw:

```xml
<w:r><w:rPr><w:vanish/></w:rPr>
  <w:t>- the reserve bidder is Wykonawca B -</w:t></w:r>
```

No print of this document shows it. The characters are in the file.

## Why this file exists

The reader took every `w:t` in the paragraph and did not look at `w:rPr`, so
the hidden run was folded into the body. The report then said it had **searched
the text and found nothing hidden** — about a file holding a sentence nobody
can see, which is the one thing this tool must never say.

The second cost is quieter and worse. Text in `units` is what the metadata
detector compares its values against, so a name in a hidden run counted as
*shown*, and `undisclosed-metadata` would have stayed silent about a field
naming somebody the page does not.

The same defect was found in `.doc` a week earlier, while the `WordDocument`
reader was being written, and fixed there first.

Everything in the metadata and the text is invented.
