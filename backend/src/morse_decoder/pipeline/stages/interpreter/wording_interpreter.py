from collections.abc import AsyncIterable, AsyncIterator

from morse_decoder.config import InterpreterSettings
from morse_decoder.pipeline.dto import CorrectedText, MorseElement
from morse_decoder.pipeline.stages.interpreter.impl.assembly import (
    TextAssembler,
    role_of,
)
from morse_decoder.pipeline.stages.interpreter.impl.lattice import BreakPrior
from morse_decoder.pipeline.stages.interpreter.impl.letter_decoder import LetterDecoder
from morse_decoder.pipeline.stages.interpreter.impl.lexicon import lexicon_for
from morse_decoder.pipeline.stages.interpreter.impl.morse_normalizer import (
    MorseNormalizer,
)
from morse_decoder.pipeline.stages.interpreter.impl.spacing import Marks, Piece, Writer
from morse_decoder.pipeline.stages.interpreter.impl.word_costs import WordPrice
from morse_decoder.pipeline.stages.interpreter.impl.word_segmenter import WordSegmenter
from morse_decoder.pipeline.stages.interpreter.interface import Interpreter


class WordingInterpreter(Interpreter):
    """Normalization, then the ITU alphabet, then the words the letters spell.

    The third of the interpreter's stages, and the first to publish something
    a reader can take at face value. Where the timing stage put the word gaps
    is treated as evidence rather than instruction: a stretched character gap
    reports a break between every letter and a hurried fist reports none, so
    the words are settled against what the language actually says instead.
    """

    def __init__(self, settings: InterpreterSettings) -> None:
        self._normalizer = MorseNormalizer()
        self._decoder = LetterDecoder()
        self._assembler = TextAssembler(_segmenter(settings), Marks())
        self._writer = Writer()

    async def process(
        self, elements: AsyncIterable[MorseElement]
    ) -> AsyncIterator[CorrectedText]:
        async for piece in self._pieces(elements):
            yield CorrectedText(text=self._writer.write(piece))

    async def _pieces(
        self, elements: AsyncIterable[MorseElement]
    ) -> AsyncIterator[Piece]:
        async for symbol in self._normalizer.process(elements):
            token = self._decoder.decode(symbol)
            for piece in role_of(token).absorb(token, self._assembler):
                yield piece
        for piece in self._assembler.close():
            yield piece


def _segmenter(settings: InterpreterSettings) -> WordSegmenter:
    lexicon = lexicon_for(settings.language)
    return WordSegmenter(
        price=WordPrice(lexicon),
        prior=BreakPrior(settings.join_penalty, settings.split_penalty),
        lexicon=lexicon,
    )
