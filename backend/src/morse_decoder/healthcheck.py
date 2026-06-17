import urllib.request

from morse_decoder.config import settings

urllib.request.urlopen(
    f"http://127.0.0.1:{settings.server.port}/health", timeout=5
)
