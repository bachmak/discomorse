from pydantic_settings import BaseSettings


class Plugin[SettingsT: BaseSettings]:
    """Construction concern: a plugin is built from its typed settings object.

    The behavioral interfaces in `base.py` bind `SettingsT` to their stage's
    settings type, so each concrete plugin inherits a constructor that requires
    exactly that type. Validation already happened when `Settings` loaded, so a
    plugin only ever receives a valid settings object — never a raw mapping.
    """

    def __init__(self, settings: SettingsT) -> None:
        self._settings = settings
