import json

from morse_decoder.api.events import (
    inbound_event_json_schema,
    outbound_event_json_schema,
)

print(
    json.dumps(
        {
            "server": outbound_event_json_schema(),
            "client": inbound_event_json_schema(),
        },
        indent=2,
        sort_keys=True,
    )
)
