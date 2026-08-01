"""Reproduces the inter-character gap collapse caused by keying debouncer skew.

Synthesizes its own audio, so the failure reproduces from the printed parameters
alone and needs no committed fixtures. Reports the decoded morse against the
reference encoding and the span measurements behind the misclassification.

    uv run python scripts/repro_debounce_skew.py
"""

import asyncio
from collections.abc import Sequence

from span_trace import Case, Decoding, Outcome, SignalSpec, SpanRecord

from morse_decoder.config import KeyingDebouncerSettings


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values)


class SkewReport:
    """Measured duration of each span category against its exact duration."""

    def __init__(self, records: Sequence[SpanRecord], dit: float) -> None:
        self._records = records
        self._dit = dit

    def render(self) -> str:
        return "\n".join(["  span      exact   measured     skew", *self._rows()])

    def _rows(self) -> list[str]:
        return [self._row(kind) for kind in sorted(self._kinds())]

    def _kinds(self) -> set[str]:
        return {record.kind(self._dit) for record in self._records}

    def _row(self, kind: str) -> str:
        matching = [r for r in self._records if r.kind(self._dit) == kind]
        exact = matching[0].true_units(self._dit) * self._dit
        measured = _mean([r.span.duration for r in matching])
        skew = _mean([r.skew_seconds(self._dit) for r in matching])
        return (
            f"  {kind:8} {exact * 1000:6.0f}ms {measured * 1000:8.1f}ms "
            f"{skew * 1000:+7.1f}ms"
        )


class MarginReport:
    """How close each inter-character gap came to being read as intra-character."""

    def __init__(
        self, records: Sequence[SpanRecord], dit: float, threshold: float
    ) -> None:
        self._records = records
        self._dit = dit
        self._threshold = threshold

    def render(self) -> str:
        margins = [self._margin(record) for record in self._inter_char_gaps()]
        wrong = sum(1 for margin in margins if margin < 0)
        return (
            f"  inter-char gaps: {len(margins)}, misread as intra-char: {wrong}\n"
            f"  margin (gap - {self._threshold} x unit): "
            f"min {min(margins) * 1000:+.1f}ms, max {max(margins) * 1000:+.1f}ms"
        )

    def _inter_char_gaps(self) -> list[SpanRecord]:
        return [
            record
            for record in self._records
            if not record.span.on and record.true_units(self._dit) == 3
        ]

    def _margin(self, record: SpanRecord) -> float:
        return record.span.duration - self._threshold * record.unit


class CaseReport:
    """One case's decode, verdict, and the measurements explaining it."""

    def __init__(self, spec: SignalSpec, case: Case, decoding: Decoding) -> None:
        self._spec = spec
        self._case = case
        self._decoding = decoding

    def render(self, outcome: Outcome) -> str:
        dit = self._spec.dit_seconds
        return "\n".join(
            [
                f"--- {self._case.label} ---",
                f"  expected  {self._spec.reference()}",
                f"  decoded   {outcome.morse}",
                f"  verdict   {self._verdict(outcome)}",
                "",
                SkewReport(outcome.records, dit).render(),
                "",
                MarginReport(
                    outcome.records, dit, self._decoding.inter_char_threshold
                ).render(),
            ]
        )

    def _verdict(self, outcome: Outcome) -> str:
        reference = self._spec.reference()
        if outcome.morse == reference:
            return "exact match"
        if reference.startswith(outcome.morse):
            return "correct but truncated (final element never flushed)"
        return "MISMATCH"


_SPEC = SignalSpec(
    message="PETER DICTATES TO HIS COMPUTER",
    freq_hz=500.0,
    wpm=20.0,
    sample_rate=8000,
)

_CASES = (
    Case("debounce on (shipped defaults)", KeyingDebouncerSettings()),
    Case(
        "debounce off (control)",
        KeyingDebouncerSettings(debounce_rise_seconds=0.0, debounce_fall_seconds=0.0),
    ),
)


async def _report(spec: SignalSpec) -> str:
    sections = [spec.describe()]
    for case in _CASES:
        decoding = Decoding(spec, case)
        outcome = await decoding.run()
        sections.append(CaseReport(spec, case, decoding).render(outcome))
    return "\n\n".join(sections)


def main() -> None:
    print(asyncio.run(_report(_SPEC)))


if __name__ == "__main__":
    main()
