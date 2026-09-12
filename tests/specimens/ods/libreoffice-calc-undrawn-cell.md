# `libreoffice-calc-undrawn-cell.ods`

**Producer:** LibreOffice 24.2 Calc. The same source as
[`xlsx/libreoffice-calc-undrawn-cell.xlsx`](../xlsx/libreoffice-calc-undrawn-cell.md),
written by the same script into the other family.

## The same trick, stated a completely different way

A `.xlsx` makes a reader resolve a chain — cell to style to format id to
format code — before it can tell that a cell prints nothing. OpenDocument
states both facts **on the cell itself**:

```xml
<table:table-cell office:value-type="float" office:value="250000"><text:p/></table:table-cell>
```

What it holds is an attribute. What it draws is the element content, and it is
empty. No style has to be resolved at all.

## And it failed in the opposite direction

Where the `.xlsx` reader read the value and reported it as a figure on the
sheet, this one took the empty `<text:p/>`, decided the cell had nothing in
it, and **dropped 250,000 entirely**. The workbook came back with nothing
found — not because it had been searched, but because the only place the
number lived was never looked at.

Two readers, one trick, wrong in opposite directions: one claims a hidden
figure is visible, the other loses it. Both are the same mistake underneath —
what a cell stores and what it draws are different things.

Everything in the text and the numbers is invented.
