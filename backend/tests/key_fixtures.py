"""The key the keying stages pass around, read back as plain flags."""

from morse_decoder.pipeline.dto import DigitalTone


def flags(samples: tuple[DigitalTone, ...]) -> tuple[bool, ...]:
    """The side of the key each sample was read on."""
    return tuple(sample.on for sample in samples)
