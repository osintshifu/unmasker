# `libreoffice-calc-undrawn-cell.xlsx`

**Producer:** LibreOffice 24.2 Calc. Built by
[`sources/build_undrawn_cell.py`](../sources/build_undrawn_cell.py), which
writes this and
[`ods/libreoffice-calc-undrawn-cell.ods`](../ods/libreoffice-calc-undrawn-cell.ods)
from one source.

## What a person sees

| | |
| :--- | :--- |
| Reserve price | *(empty)* |
| Bids received | 4 |

## What is stored inside

`B1` holds **250000**. The cell is not hidden, its row is not hidden and its
column is not hidden — it simply carries a number format that draws nothing.

The chain runs through three files' worth of indirection inside the one
archive:

```
<c r="B1" s="1">           the cell names style 1
<cellXfs> … <xf numFmtId="165">   style 1 names format 165
<numFmt numFmtId="165" formatCode="&quot;&quot;"/>
```

**LibreOffice writes the format as `""`, an empty literal.** The folklore of
this trick is `;;;`, which is what Excel writes, and a reader that matched the
string would find nothing here. So the rule is about what a *section* of a
format prints, not about a particular code — and it is deliberately
conservative, answering *draws nothing* only when there is literally nothing
left to print, because claiming a visible figure is hidden is the worse of the
two mistakes.

`;;;` itself is handled by the same rule and **not verified against a real
file**: no available producer writes one.

## What this cost before it was read

The value was read out of `<v>250000</v>` and reported as text on the sheet —
so the figure somebody had gone to the trouble of hiding was quoted back as
though it were printed on the page, and counted as visible text for every
detector downstream.

The second row is the control. An ordinary number in an ordinary format must
go on being read as something a person can see, and a format rule that
swallowed real figures would be worse than the gap it was written to close.

Everything in the text and the numbers is invented.
