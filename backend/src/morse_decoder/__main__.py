import uvicorn

from morse_decoder.api.routes import app
from morse_decoder.config import global_settings

uvicorn.run(app, host=global_settings.server.host, port=global_settings.server.port)
