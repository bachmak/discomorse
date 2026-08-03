import urllib.request

from morse_decoder.config import Settings

urllib.request.urlopen(f"http://127.0.0.1:{Settings().server.port}/health", timeout=5)
