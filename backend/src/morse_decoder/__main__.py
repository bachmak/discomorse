import uvicorn

from morse_decoder.api.routes import app
from morse_decoder.config import Settings

_server = Settings().server

uvicorn.run(app, host=_server.host, port=_server.port)
