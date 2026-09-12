# `libreoffice-writer-hidden-run.odt`

**Producer:** LibreOffice 24.2 Writer. The same source document as
[`docx/libreoffice-writer-hidden-run.docx`](../docx/libreoffice-writer-hidden-run.docx),
written by the same script into the other container.

## What a person sees

The same two lines, and the same sentence missing from the second one.

## What is stored inside

```xml
<style:style style:name="T1" style:family="text">
  <style:text-properties text:display="none"/></style:style>
...
<text:span text:style-name="T1">- the reserve bidder is Wykonawca B -</text:span>
```

## Why the pair is worth having

**OpenDocument hides text with a style; Word hides it with the run.** Word's
`w:vanish` sits on the run itself, so a reader that has the run has the answer.
Here the run carries only a style *name*, and nothing in the body says what
that name means — the styles have to be read first, and through
`style:parent-style-name` as well, because a style that inherits the property
hides exactly as thoroughly as one that states it.

A reader written against one format and pointed at the other finds nothing and
says so cheerfully.

Everything in the metadata and the text is invented.
