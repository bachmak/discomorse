from dataclasses import dataclass


@dataclass(frozen=True)
class KeyingThresholds:
    on: float
    off: float
