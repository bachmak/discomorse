"""Runs one test config: generated signal in, decoded morse judged on the way out.

Drives `official_generator.py` with the settings the config names,
writes the WAV to a temp directory, and pushes it through the very pipeline
`decode_file.py` uses. The decoded notation is then held against the config's
expectation; a shortfall fails the run.

    uv run python scripts/run_test_config.py test_configs/clean_baseline.json
"""

from __future__ import annotations

import argparse
import asyncio
import subprocess
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from tempfile import TemporaryDirectory

from decode_file import Excerpt, FileDecoding, Report
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from morse_decoder.config import PipelineSettings, Settings, StreamSettings

_GENERATOR = Path(__file__).with_name("official_generator.py")
_QRN_OFF_DB = 35.0  # the generator reads anything from here up as noise-free


class SignalSpec(BaseModel):
    """The knobs `official_generator.py` offers on its command line."""

    model_config = ConfigDict(extra="forbid")

    input_text: str
    wpm: int = Field(default=20, gt=0)
    pitch_hz: int = Field(default=600, gt=0)
    qrn_snr_db: float = Field(default=_QRN_OFF_DB, ge=0)
    qrm_level: float = Field(default=0.0, ge=0, le=1)
    qsb_depth: float = Field(default=0.0, ge=0, le=1)
    qsb_rate_hz: float = Field(default=0.25, gt=0)
    sample_rate: int = Field(default=44_100, gt=0)

    def cli_options(self) -> tuple[str, ...]:
        flags: dict[str, str | int | float] = {
            "--text": self.input_text,
            "--wpm": self.wpm,
            "--freq": self.pitch_hz,
            "--qrn": self.qrn_snr_db,
            "--qrm": self.qrm_level,
            "--qsb": self.qsb_depth,
            "--qsb-rate": self.qsb_rate_hz,
            "--sample-rate": self.sample_rate,
        }
        return tuple(str(part) for pair in flags.items() for part in pair)

    def describe(self) -> str:
        return (
            f'"{self.input_text}" @ {self.wpm} wpm, {self.pitch_hz} Hz, '
            f"{self.sample_rate} Hz sampling, QRN {self.qrn_snr_db} dB, "
            f"QRM {self.qrm_level}, QSB {self.qsb_depth} @ {self.qsb_rate_hz} Hz"
        )


class TestConfig(BaseModel):
    """A signal to generate and the morse the pipeline owes us for it.

    `min_similarity` is the share of the expected notation a run has to
    reproduce. It stays at 1.0 for signals the decoder is meant to read
    perfectly and drops only where a config deliberately degrades the signal.
    """

    model_config = ConfigDict(extra="forbid")

    signal: SignalSpec
    expected_morse: str
    min_similarity: float = Field(default=1.0, gt=0, le=1)

    @classmethod
    def load(cls, path: Path) -> TestConfig:
        try:
            return cls.model_validate_json(path.read_bytes())
        except ValidationError as invalid:
            raise SystemExit(f"{path} is no usable test config:\n{invalid}") from None


@dataclass(frozen=True)
class Transcript:
    """Morse notation with its spacing normalized, so two runs compare cleanly."""

    notation: str

    @classmethod
    def of(cls, raw: str) -> Transcript:
        return cls(" ".join(raw.split()))

    def similarity_to(self, other: Transcript) -> float:
        return SequenceMatcher(None, other.notation, self.notation).ratio()


class Verdict(ABC):
    """What a comparison concluded, and what that makes of the run."""

    @property
    @abstractmethod
    def label(self) -> str: ...

    @property
    @abstractmethod
    def exit_code(self) -> int: ...


class Match(Verdict):
    """The decode reproduced enough of the expected notation."""

    @property
    def label(self) -> str:
        return "match"

    @property
    def exit_code(self) -> int:
        return 0


class Mismatch(Verdict):
    """The decode fell short of what the config demands."""

    @property
    def label(self) -> str:
        return "MISMATCH - decoded morse falls short of the expectation"

    @property
    def exit_code(self) -> int:
        return 1


@dataclass(frozen=True)
class Comparison:
    """Expected notation against decoded notation, judged at a floor."""

    expected: Transcript
    decoded: Transcript
    floor: float

    def similarity(self) -> float:
        return self.decoded.similarity_to(self.expected)

    def verdict(self) -> Verdict:
        return Match() if self.similarity() >= self.floor else Mismatch()


class MorseGenerator:
    """Official generator, driven through its command line."""

    def __init__(self, script: Path) -> None:
        self._script = script

    def render(self, spec: SignalSpec, target: Path) -> Path:
        result = subprocess.run(self._command(spec, target), stdout=subprocess.DEVNULL)
        if result.returncode:
            raise SystemExit(f"{self._script.name} exited {result.returncode}")
        return target

    def _command(self, spec: SignalSpec, target: Path) -> list[str]:
        return [
            sys.executable,
            str(self._script),
            "--no-ui",
            *spec.cli_options(),
            "--output",
            str(target),
        ]


class ConfigRun:
    """One pass: config → generated WAV → pipeline → comparison."""

    def __init__(
        self, config: TestConfig, settings: Settings, generator: MorseGenerator
    ) -> None:
        self._config = config
        self._settings = settings
        self._generator = generator

    async def compare(self) -> Comparison:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "signal.wav"
            self._generator.render(self._config.signal, path)
            return self._against(await self._decode(path))

    async def _decode(self, path: Path) -> Transcript:
        excerpt = Excerpt("morse", "morse_elements")
        await FileDecoding(path, self._settings, Report((excerpt,))).run()
        return Transcript.of(excerpt.text())

    def _against(self, decoded: Transcript) -> Comparison:
        return Comparison(
            expected=Transcript.of(self._config.expected_morse),
            decoded=decoded,
            floor=self._config.min_similarity,
        )


class RunReport:
    """What one run is worth printing, whether it passed or not."""

    def __init__(self, path: Path, spec: SignalSpec, comparison: Comparison) -> None:
        self._path = path
        self._spec = spec
        self._comparison = comparison

    def render(self, verdict: Verdict) -> str:
        return "\n".join(
            [
                f"config:     {self._path}",
                f"signal:     {self._spec.describe()}",
                f"expected:   {self._comparison.expected.notation}",
                f"decoded:    {self._comparison.decoded.notation}",
                f"similarity: {self._comparison.similarity():.2f} "
                f"(floor {self._comparison.floor:.2f})",
                f"verdict:    {verdict.label}",
            ]
        )


def _parse_config_path() -> Path:
    parser = argparse.ArgumentParser(
        description="Generate a morse signal from a test config and decode it."
    )
    parser.add_argument("config", type=Path, help="test config JSON to run")
    path = Path(parser.parse_args().config)
    if not path.is_file():
        parser.error(f"no such config: {path}")
    return path


def _settings() -> Settings:
    return Settings(
        pipeline=PipelineSettings(stream_settings=StreamSettings(morse_elements=True))
    )


def main() -> int:
    path = _parse_config_path()
    config = TestConfig.load(path)
    run = ConfigRun(config, _settings(), MorseGenerator(_GENERATOR))
    comparison = asyncio.run(run.compare())
    verdict = comparison.verdict()
    print(RunReport(path, config.signal, comparison).render(verdict))
    return verdict.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
