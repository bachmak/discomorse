import json

from morse_decoder.api.messages import (
    inbound_message_json_schema,
    outbound_message_json_schema,
)

print(
    json.dumps(
        {
            "server": outbound_message_json_schema(),
            "client": inbound_message_json_schema(),
        },
        indent=2,
        sort_keys=True,
    )
)
