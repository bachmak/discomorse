from typing import get_args

import pytest

from morse_decoder.api.helpers import subscription_to_settings
from morse_decoder.api.messages import ChannelName, SubscriptionMessage
from morse_decoder.config import StreamSettings

_ALL_CHANNELS: tuple[ChannelName, ...] = get_args(ChannelName.__value__)


def _streams(*channels: ChannelName) -> StreamSettings:
    return subscription_to_settings(SubscriptionMessage(channels=set(channels)))


def _enabled(streams: StreamSettings) -> set[str]:
    return {name for name in StreamSettings.model_fields if getattr(streams, name)}


def test_every_channel_names_a_stream_flag() -> None:
    assert set(_ALL_CHANNELS) == set(StreamSettings.model_fields)


@pytest.mark.parametrize(
    "channels, want",
    [
        pytest.param((), set(), id="nothing-subscribed"),
        pytest.param(("spectrums",), {"spectrums"}, id="one-channel"),
        pytest.param(
            ("morse_elements", "corrected_text"),
            {"morse_elements", "corrected_text"},
            id="two-channels",
        ),
        pytest.param(_ALL_CHANNELS, set(_ALL_CHANNELS), id="everything"),
    ],
)
def test_subscription_enables_exactly_the_channels_it_names(
    channels: tuple[ChannelName, ...], want: set[str]
) -> None:
    assert _enabled(_streams(*channels)) == want
