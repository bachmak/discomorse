from collections.abc import AsyncIterable, AsyncIterator

from morse_decoder.config import TextCorrectorSettings
from morse_decoder.pipeline.dto import CorrectedText, Token
from morse_decoder.pipeline.stages.text_corrector.impl.assembly import (
    TextAssembler,
    role_of,
)
from morse_decoder.pipeline.stages.text_corrector.impl.lattice import BreakPrior
from morse_decoder.pipeline.stages.text_corrector.impl.lexicon import lexicon_for
from morse_decoder.pipeline.stages.text_corrector.impl.spacing import (
    Marks,
    Piece,
    Writer,
)
from morse_decoder.pipeline.stages.text_corrector.impl.word_costs import WordPrice
from morse_decoder.pipeline.stages.text_corrector.impl.word_segmenter import (
    WordSegmenter,
)
from morse_decoder.pipeline.stages.text_corrector.interface import TextCorrector


class WordingTextCorrector(TextCorrector):
    """Groups the decoded tokens into the words the language says they spell.

    Where the timing stage put the word gaps is treated as evidence rather
    than instruction: a stretched character gap reports a break between every
    letter and a hurried fist reports none, so the words are settled against
    what the language actually says instead.
    """

    def __init__(self, settings: TextCorrectorSettings) -> None:
        self._assembler = TextAssembler(_segmenter(settings), Marks())
        self._writer = Writer()

    async def process(
        self, tokens: AsyncIterable[Token]
    ) -> AsyncIterator[CorrectedText]:
        async for piece in self._pieces(tokens):
            yield CorrectedText(text=self._writer.write(piece))

    async def _pieces(self, tokens: AsyncIterable[Token]) -> AsyncIterator[Piece]:
        async for token in tokens:
            for piece in role_of(token).absorb(token, self._assembler):
                yield piece
        for piece in self._assembler.close():
            yield piece


def _segmenter(settings: TextCorrectorSettings) -> WordSegmenter:
    lexicon = lexicon_for(settings.language)
    return WordSegmenter(
        price=WordPrice(lexicon),
        prior=BreakPrior(settings.join_penalty, settings.split_penalty),
        lexicon=lexicon,
    )
