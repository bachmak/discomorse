from morse_decoder.pipeline.dto import Transcription
from morse_decoder.pipeline.stages.interface import OneToOneStage
from morse_decoder.pipeline.stages.interpreter.tokens import Token


class TokenTranscriber(OneToOneStage[Token, Transcription]):
    """Reads the decoded tokens out as the message they spell.

    Holds nothing: the normalizer has already placed the breaks between words,
    so each token carries its own spacing and owes none to the one behind it.
    """

    def process_single(self, token: Token) -> Transcription:
        return Transcription(text=token.text())
