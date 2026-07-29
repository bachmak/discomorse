import json

from morse_decoder.api.wire import (
    client_message_json_schema,
    server_message_json_schema,
)

print(
    json.dumps(
        {
            "server": server_message_json_schema(),
            "client": client_message_json_schema(),
        },
        indent=2,
        sort_keys=True,
    )
)
