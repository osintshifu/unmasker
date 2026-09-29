"""Hidden slides and speaker notes, and what to report about them.

A deck conceals two ways no other container does.

A **slide marked hidden** is skipped when the deck is shown and travels with
the file exactly as it was authored - the slide that was cut before the meeting
and never deleted.

A **speaker note** was never on the screen at all. That is what notes are for,
and it is why people write candid things in them, and why the candid thing goes
out with the file.

**Text parked beside the slide** is the third. The pasteboard around a slide
is working space, and a line dragged onto it is gone from the projector, the
print and the PDF - and still in the shape tree. Nobody has to mean anything by
it, which is why it is still there when the deck goes out.

A **shape drawn over text** is the fourth, and it is the oldest failed
redaction there is. It can be checked here without rendering anything, because
unlike a word processor a slide says exactly where everything is: absolute
coordinates against a known slide size, painted in document order. What it does
*not* say is where each character sits inside its text box, so the claim is
only ever as strong as the geometry supports - and the finding says which.

All three are the same statement this tool makes everywhere: in the file, not
on the thing anybody looked at. So the record and the findings live here and
each format contributes only a reader - the arrangement `revisions.py` and
`sheets.py` already use.

## Three rules, and one of them was a decision

**A hidden slide is one finding, quoting everything on it.** Not one per text
frame: a slide is what a person recognises, and the producers disagree about
how many frames a slide has anyway.

**Notes on a hidden slide are not reported separately.** The slide is already
the finding, and saying its notes are also unseen tells a reader nothing they
did not just read - the same rule that keeps a hidden sheet from also reporting
its hidden rows.

**Speaker notes are a finding, not a remark.** This one was a judgement. A note
is a designed, labelled part of the format and every deck has the field; it
would have been defensible to remark on them instead. They are reported because
a note is content in the file that is not on the thing an audience saw, which
is the definition this whole tool runs on - and because unlike a `Producer`
string, an *empty* notes field is the common case, so this does not fire on
every deck ever written.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .findings import Basis, Finding, Location

#: Below this share of a text box, an overlapping shape is a corner touching
#: it rather than something drawn over it. A quarter is low on purpose: what
#: this gates is the *circumstantial* half of the finding, where the report
#: already says the file does not settle it, and painting order has already
#: thrown out the ordinary case of text sitting on a coloured band.
LEAST_OVERLAP = 0.25

#: A fill this large is the slide's background, not something put over
#: anything. The same rule the PDF detector applies to a page-sized shape.
BACKGROUND = 0.9


@dataclass(frozen=True)
class Shape:
    """One shape on a slide: where it is, when it was painted, what it holds.

    Coordinates are in points, converted by the reader, so nothing here has to
    know that OOXML counts in EMU and OpenDocument in centimetres.
    """

    left: float
    top: float
    width: float
    height: float
    order: int
    """Position in the slide's shape tree, which is painting order: a higher
    number is drawn later, and therefore on top."""

    text: str = ""
    fill: str = ""
    """The fill colour as the file states it, or empty where the shape is not
    filled. Any fill hides what is behind it; the colour is reported because a
    reader deciding what they are looking at wants it, not because this makes
    a judgement from it."""

    @property
    def area(self) -> float:
        return max(self.width, 0.0) * max(self.height, 0.0)

    def overlap(self, other: Shape) -> float:
        """The area the two share."""
        wide = min(self.left + self.width, other.left + other.width) - max(
            self.left, other.left
        )
        tall = min(self.top + self.height, other.top + other.height) - max(
            self.top, other.top
        )
        return wide * tall if wide > 0 and tall > 0 else 0.0

    def beside(self, width: float, height: float) -> bool:
        """Whether the shape lies entirely off a slide of this size.

        Entirely, and nothing less. A title box wider than its slide is
        ordinary layout, and a slide gives no glyph positions - so an overhang
        cannot be told from a sentence pushed half off the edge, and reporting
        one would fire on decks that hide nothing.
        """
        if width <= 0 or height <= 0:
            return False
        return (
            self.left >= width
            or self.top >= height
            or self.left + self.width <= 0
            or self.top + self.height <= 0
        )

    def contains(self, other: Shape) -> bool:
        return (
            self.left <= other.left
            and self.top <= other.top
            and self.left + self.width >= other.left + other.width
            and self.top + self.height >= other.top + other.height
        )


@dataclass(frozen=True)
class Slide:
    number: int
    """1-based, and it is the number the person who hid it saw."""

    text: str = ""
    """What is drawn on the slide, frames joined in document order."""

    notes: str = ""
    """The speaker's own copy. Never on the screen, by design."""

    hidden: bool = False
    title: str | None = None

    shapes: tuple[Shape, ...] = ()
    """Every shape on the slide, in painting order. Empty where the reader
    could not measure the slide, which is not the same as a slide with nothing
    on it - `remarks` says which."""

    width: float = 0.0
    height: float = 0.0
    """The slide itself, in points. A shape is only background-sized against
    the slide; measuring it against the largest *shape* makes every bar the
    background of its own comparison, which is what the first draft of this
    did."""


@dataclass(frozen=True)
class SlideRecord:
    slides: tuple[Slide, ...] = ()
    remarks: tuple[str, ...] = field(default_factory=tuple)

    unsearched: tuple[str, ...] = ()
    """What this reading did not cover, when the part that would have answered
    would not parse. An empty container and a container nobody could open are
    different answers, and a record carrying only `remarks` makes a caller
    tell them apart by reading prose."""

    @property
    def visible_text(self) -> str:
        """What an audience read, one slide per block.

        The hidden slides and every note are left out, which is the whole
        reason a deck needs its own reader: yielding all of it would hand the
        concealed half to the character detectors as though somebody had seen
        it, and then report the deck clean.
        """
        return "\n".join(s.text for s in self.slides if not s.hidden and s.text.strip())


def _count(text: str) -> str:
    return f"{len(text)} character" + ("" if len(text) == 1 else "s")


def hidden_slides(record: SlideRecord) -> list[Finding]:
    findings = []
    for slide in record.slides:
        if not slide.hidden:
            continue
        # Notes belong to the slide, so a hidden slide's notes are hidden with
        # it and quoted here rather than reported twice.
        carried = "  ".join(part for part in (slide.text, slide.notes) if part.strip())
        if not carried.strip():
            continue
        named = f' ("{slide.title}")' if slide.title else ""
        findings.append(
            Finding(
                detector="hidden-slide",
                basis=Basis.DIRECT,
                summary=(
                    f"slide {slide.number}{named} is marked hidden, so it is "
                    f"skipped when the deck is shown; {_count(carried)} of it "
                    "are still in the file"
                ),
                human_sees="",
                machine_reads=carried,
                location=Location(),
            )
        )
    return findings


def speaker_notes(record: SlideRecord) -> list[Finding]:
    findings = []
    for slide in record.slides:
        if slide.hidden or not slide.notes.strip():
            continue
        findings.append(
            Finding(
                detector="speaker-notes",
                basis=Basis.DIRECT,
                summary=(
                    f"slide {slide.number} carries a speaker note, which is in "
                    "the file and was never on the screen"
                ),
                human_sees="",
                machine_reads=slide.notes,
                location=Location(),
            )
        )
    return findings


def covered_text(record: SlideRecord) -> list[Finding]:
    """Text with a filled shape painted over it, afterwards.

    Painting order is what separates a redaction from an ordinary slide.
    Text on a coloured band overlaps its band exactly as a bar overlaps the
    name under it; the only difference is which was drawn first, and the file
    states it. So a fill is only ever compared against text painted *before*
    it.

    A hidden slide is left alone. It is already a finding that quotes
    everything on it, and reporting the bar as well would say a second time
    what a reader has just read - the rule a hidden sheet's rows already
    follow.

    The basis is the geometry and nothing else. Where the fill's rectangle
    contains the text box, every character of that text is behind it and the
    evidence is direct. Where it takes part of the box, the file does not say
    which characters those are - a slide stores the box, not the glyphs - so
    the finding is circumstantial and says so rather than implying a precision
    the format cannot give.
    """
    findings: list[Finding] = []
    for slide in record.slides:
        if slide.hidden or not slide.shapes:
            continue
        page = slide.width * slide.height

        for shape in slide.shapes:
            # A fill this large is the slide's background, not something put
            # over anything: it is painted first in every deck that has one,
            # but a deck that puts it last would otherwise report every frame.
            if not shape.fill or (page and shape.area >= BACKGROUND * page):
                continue

            for under in slide.shapes:
                if under.order >= shape.order or not under.text.strip():
                    continue
                shared = shape.overlap(under)
                if not shared or not under.area:
                    continue

                whole = shape.contains(under)
                share = shared / under.area
                if not whole and share < LEAST_OVERLAP:
                    continue

                findings.append(
                    Finding(
                        detector="covered-text",
                        basis=Basis.DIRECT if whole else Basis.CIRCUMSTANTIAL,
                        summary=(
                            f"{_count(under.text)} lie entirely behind a shape "
                            f"filled {shape.fill}, drawn over them on slide "
                            f"{slide.number}; the text is still in the file"
                            if whole
                            else f"a shape filled {shape.fill}, drawn over a text "
                            f"box on slide {slide.number}, covers {share:.0%} of "
                            "it; which characters are behind it is not in the "
                            "file, because a slide stores the box and not the "
                            "position of each letter"
                        ),
                        # Blocks only where every character is behind the
                        # shape. Painting the whole string black for a box
                        # half covered would draw a picture of something this
                        # cannot see - the file gives no glyph positions, so
                        # which half is hidden is not known.
                        human_sees=(
                            "\u2588" * len(under.text)
                            if whole
                            else "part of it, behind the shape"
                        ),
                        machine_reads=under.text,
                        location=Location(page=slide.number),
                    )
                )
    return findings


def offstage_text(record: SlideRecord) -> list[Finding]:
    """Text on the pasteboard: in the file, and on no slide anybody saw.

    A hidden slide is left alone, as it is everywhere else here: it is already
    a finding quoting everything on it, and saying a second time that part of
    it is off to one side tells a reader nothing they have not just read.
    """
    findings: list[Finding] = []
    for slide in record.slides:
        if slide.hidden or not slide.width:
            continue
        for shape in slide.shapes:
            if not shape.text.strip() or not shape.beside(slide.width, slide.height):
                continue
            findings.append(
                Finding(
                    detector="off-page-text",
                    basis=Basis.DIRECT,
                    summary=(
                        f"{_count(shape.text)} sit beside slide {slide.number} "
                        "rather than on it, in the working space around the "
                        "slide; no showing, print or export of this deck puts "
                        "them in front of anybody, and they are still in the file"
                    ),
                    human_sees="",
                    machine_reads=shape.text,
                    location=Location(page=slide.number),
                )
            )
    return findings


def detect(record: SlideRecord) -> list[Finding]:
    """Every presentation finding in one deck. Additive, and none outranks
    another."""
    return (
        hidden_slides(record)
        + speaker_notes(record)
        + covered_text(record)
        + offstage_text(record)
    )
