### THIS FILE IS FOR TESTING PURPOSES ONLY. DO NOT COPY OR IMPORT
### ANYTHING FROM THIS FILE INTO PRODUCTION CODE. ###


import pytest

from morse_decoder.plugins.base import Plugin, PluginConfig
from morse_decoder.plugins.factory import PluginConfigError, _build


class _WidgetConfig(PluginConfig):
    gain: float = 1.0
    label: str = "default"


class _Widget(Plugin):
    """Stand-in plugin that exposes the config it was built with."""

    Config = _WidgetConfig

    def __init__(self, config: _WidgetConfig) -> None:
        super().__init__(config)
        self.config = config


_CATALOG: dict[str, type[_Widget]] = {"widget": _Widget}


@pytest.mark.parametrize(
    ("config", "want_gain", "want_label"),
    [
        pytest.param({}, 1.0, "default", id="empty-uses-defaults"),
        pytest.param({"gain": 2.5}, 2.5, "default", id="partial-override"),
        pytest.param({"gain": 3.0, "label": "x"}, 3.0, "x", id="full-override"),
        pytest.param({"gain": "4.5"}, 4.5, "default", id="coerces-numeric-string"),
    ],
)
def test_build_validates_and_injects_config(
    config: dict[str, object], want_gain: float, want_label: str
) -> None:
    widget = _build(_CATALOG, "widget", "widget", config)

    assert widget.config.gain == want_gain
    assert widget.config.label == want_label


@pytest.mark.parametrize(
    ("config", "match"),
    [
        pytest.param({"bogus": 1}, "invalid config for widget", id="unknown-key"),
        pytest.param({"gain": "abc"}, "invalid config for widget", id="wrong-type"),
    ],
)
def test_build_rejects_bad_config(config: dict[str, object], match: str) -> None:
    with pytest.raises(PluginConfigError, match=match):
        _build(_CATALOG, "widget", "widget", config)


def test_build_raises_for_unknown_name() -> None:
    with pytest.raises(KeyError, match="Unknown widget: 'missing'"):
        _build(_CATALOG, "missing", "widget", {})
