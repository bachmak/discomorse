import urllib.request

from morse_decoder.config import global_settings

urllib.request.urlopen(
    f"http://127.0.0.1:{global_settings.server.port}/health", timeout=5
)
