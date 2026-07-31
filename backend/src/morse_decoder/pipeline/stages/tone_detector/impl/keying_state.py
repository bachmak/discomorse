from __future__ import annotations

from abc import ABC, abstractmethod

from morse_decoder.pipeline.stages.tone_detector.impl.dto import (
    KeyingSample,
    KeyingThresholds,
)


class KeyingState(ABC):
    """Small FSM to implement hysteresis between on/off states."""

    @abstractmethod
    def update(self, magnitude: float, thresholds: KeyingThresholds) -> KeyingState: ...

    @abstractmethod
    def get_keying(self) -> KeyingSample: ...


class OffState(KeyingState):
    def update(self, magnitude: float, thresholds: KeyingThresholds) -> KeyingState:
        if magnitude > thresholds.on:
            return OnState()
        return self

    def get_keying(self) -> KeyingSample:
        return KeyingSample(is_on=False)


class OnState(KeyingState):
    def update(self, magnitude: float, thresholds: KeyingThresholds) -> KeyingState:
        if magnitude < thresholds.off:
            return OffState()
        return self

    def get_keying(self) -> KeyingSample:
        return KeyingSample(is_on=True)
