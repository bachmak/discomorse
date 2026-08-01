from __future__ import annotations

from abc import ABC, abstractmethod

from morse_decoder.pipeline.stages.keying_detector.dto import KeyingThresholds


class KeyingState(ABC):
    """Small FSM to implement hysteresis between on/off states."""

    @abstractmethod
    def update(self, magnitude: float, thresholds: KeyingThresholds) -> KeyingState: ...

    @abstractmethod
    def is_on(self) -> bool: ...


class OffState(KeyingState):
    def update(self, magnitude: float, thresholds: KeyingThresholds) -> KeyingState:
        if magnitude > thresholds.on:
            return OnState()
        return self

    def is_on(self) -> bool:
        return False


class OnState(KeyingState):
    def update(self, magnitude: float, thresholds: KeyingThresholds) -> KeyingState:
        if magnitude < thresholds.off:
            return OffState()
        return self

    def is_on(self) -> bool:
        return True
