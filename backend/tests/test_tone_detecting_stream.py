"""The stages across readings: what was read last time must decide what is read now."""

import pytest
from carrier_fixtures import ANALYZER_SETTINGS, analyze
from key_fixtures import flags
from tone_detecting_fixtures import detect, read_tone, tone_detecting
from tone_fixtures import KeyedLine, PcmChunks, morse_line

_LINE = morse_line()
_PCM = _LINE.pcm()


@pytest.mark.parametrize(
    "chunks",
    [
        pytest.param(2, id="two-chunks"),
        pytest.param(3, id="three-chunks"),
        pytest.param(17, id="seventeen-chunks"),
        pytest.param(101, id="a-hundred-and-one-chunks"),
    ],
)
async def test_the_line_reads_back_the_same_however_the_audio_is_chunked(
    chunks: int,
) -> None:
    assert await read_tone(_PCM, chunks) == await read_tone(_PCM)


async def test_every_spectrum_yields_one_sample_stamped_with_its_own_time() -> None:
    spectrums = await analyze(_PCM)

    samples = await detect(spectrums)

    assert tuple(sample.ts for sample in samples) == tuple(
        spectrum.ts for spectrum in spectrums
    )


async def test_a_chunk_too_short_to_fill_a_frame_reads_back_nothing() -> None:
    short = _PCM[: ANALYZER_SETTINGS.n_fft - 1]

    for chunk in PcmChunks(short):
        assert await tone_detecting().feed(chunk) == ()


async def test_a_locked_carrier_keys_the_next_reading_from_its_first_sample() -> None:
    lead_in, held = tuple(PcmChunks(KeyedLine().mark(4).pcm(), count=2))
    warmed = tone_detecting()

    await warmed.feed(lead_in)

    assert flags(await warmed.feed(held))[0]
    assert not flags(await tone_detecting().feed(held))[0]
