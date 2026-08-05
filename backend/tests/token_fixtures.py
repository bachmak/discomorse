"""Builders for the tokens the correcting stage is driven with.

A test writes the message it means and gets back the tokens the decoding stage
would have handed over for it: one per character, with the word gaps the
timing stage claimed to hear standing between them.
"""

from morse_decoder.pipeline.dto import Token

WORD_GAP = Token(value=" ")


def keyed_tokens(message: str) -> list[Token]:
    """What a clean fist produces: a gap between words and nowhere else."""
    return _joined([[Token(value=char) for char in word] for word in message.split()])


def spelled_tokens(message: str) -> list[Token]:
    """The same characters, with a gap standing between every one of them.

    What a character gap stretched past the word threshold makes the timing
    stage report, so every character arrives looking like a word of its own.
    """
    return _joined([[Token(value=char)] for char in message if not char.isspace()])


def _joined(groups: list[list[Token]]) -> list[Token]:
    joined: list[Token] = []
    for group in groups:
        if joined:
            joined.append(WORD_GAP)
        joined.extend(group)
    return joined
