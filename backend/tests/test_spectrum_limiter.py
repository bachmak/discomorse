"""What the limiter lets through to the stages behind it, and what it cuts away."""

import pytest
from carrier_fixtures import spectrum
from limiter_fixtures import MAX_HZ, MIN_HZ, kept, limit, limited, limiter

_LOUD = 1.0


@pytest.mark.parametrize(
    "bins, want_frequencies",
    [
        pytest.param({700.0: _LOUD}, (700.0,), id="inside"),
        pytest.param({MIN_HZ: _LOUD}, (MIN_HZ,), id="lower-edge-included"),
        pytest.param({MAX_HZ: _LOUD}, (MAX_HZ,), id="upper-edge-included"),
        pytest.param({MIN_HZ - 1: _LOUD, 700.0: _LOUD}, (700.0,), id="just-below-cut"),
        pytest.param({MAX_HZ + 1: _LOUD, 700.0: _LOUD}, (700.0,), id="just-above-cut"),
        pytest.param(
            {1.0: _LOUD, 700.0: _LOUD, 3_000.0: _LOUD}, (700.0,), id="far-outside-cut"
        ),
    ],
)
async def test_the_limiter_keeps_only_the_bins_its_band_covers(
    bins: dict[float, float], want_frequencies: tuple[float, ...]
) -> None:
    assert await kept(bins) == want_frequencies


async def test_the_limiter_keeps_the_levels_of_the_bins_it_lets_through() -> None:
    one = await limited({100.0: _LOUD, 700.0: 0.3, 900.0: 0.6})

    assert tuple(tone.magnitude for tone in one.magnitudes) == (0.3, 0.6)


async def test_the_limiter_stamps_the_limited_spectrum_with_its_own_time() -> None:
    one = spectrum({700.0: _LOUD}, at_second=0.5)

    assert (await limit((one,)))[0].ts == one.ts


async def test_a_narrow_band_cuts_the_bins_just_outside_it() -> None:
    bins = {699.0: _LOUD, 700.0: 0.1, 701.0: _LOUD}

    assert await kept(bins, spectrum_limiter=limiter(699.5, 700.5)) == (700.0,)


@pytest.mark.parametrize(
    "bins",
    [
        pytest.param({100.0: _LOUD, 200.0: 0.5}, id="all-bins-below-the-band"),
        pytest.param({2_000.0: _LOUD, 3_000.0: 0.5}, id="all-bins-above-the-band"),
        pytest.param({}, id="no-bins-at-all"),
    ],
)
async def test_a_spectrum_missing_the_band_is_rejected(
    bins: dict[float, float],
) -> None:
    with pytest.raises(ValueError, match="no spectrum bin"):
        await kept(bins)


async def test_one_limiter_reads_a_spectrum_as_a_fresh_one_would() -> None:
    """The limiter carries no state: a used one still cuts the same band."""
    bins = {100.0: _LOUD, 700.0: 0.3}
    used = limiter()
    await kept(bins, spectrum_limiter=used)

    assert await kept(bins, spectrum_limiter=used) == await kept(bins)
