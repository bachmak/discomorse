from morse_decoder.api.messages import SubscriptionMessage
from morse_decoder.config import StreamSettings


def subscription_to_settings(message: SubscriptionMessage) -> StreamSettings:
    return StreamSettings(
        **dict.fromkeys(message.channels, True),
    )
