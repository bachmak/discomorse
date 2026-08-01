"""The key the keying stages pass around, read back as plain flags."""

from morse_decoder.pipeline.dto import ToneSample


def flags(samples: tuple[ToneSample, ...]) -> tuple[bool, ...]:
    """The side of the key each sample was read on."""
    return tuple(sample.on for sample in samples)
