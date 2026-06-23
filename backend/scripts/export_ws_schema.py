import json

from morse_decoder.api.wire import server_message_json_schema

print(json.dumps(server_message_json_schema(), indent=2, sort_keys=True))
