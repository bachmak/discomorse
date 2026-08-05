PRES.data = (() => {
  const stages = [
    { id: "sa", name: "SpectrumAnalyzer", impl: "STFTSpectrumAnalyzer", tIn: "PcmChunk", tOut: "ToneSpectrum", oneToOne: false },
    { id: "sl", name: "SpectrumLimiter", impl: "StaticSpectrumLimiter", tIn: "ToneSpectrum", tOut: "ToneSpectrum", oneToOne: true },
    { id: "cs", name: "CarrierSource", impl: "PeakCarrierSource", tIn: "ToneSpectrum", tOut: "CarrierSample", oneToOne: false },
    { id: "ne", name: "NoiseEstimator", impl: "PercentileNoiseEstimator", tIn: "ToneSpectrum", tOut: "NoiseSample", oneToOne: true },
    { id: "kd", name: "KeyingDetector", impl: "AdaptiveKeyingDetector", tIn: "CarrierNoiseSample", tOut: "DigitalTone", oneToOne: true },
    { id: "kb", name: "KeyingDebouncer", impl: "TimedKeyingDebouncer", tIn: "DigitalTone", tOut: "DigitalTone", oneToOne: false },
    { id: "td", name: "TimingDecoder", impl: "AdaptiveThresholdDecoder", tIn: "DigitalTone", tOut: "MorseElement", oneToOne: false },
    { id: "sd", name: "SymbolDecoder", impl: "ItuSymbolDecoder", tIn: "MorseElement", tOut: "Token", oneToOne: false },
    { id: "tc", name: "TextCorrector", impl: "WordingTextCorrector", tIn: "Token", tOut: "CorrectedText", oneToOne: false },
  ];

  const subscribed = new Set([
    "spectrums",
    "debounced_tones",
    "morse_elements",
    "decoded_symbols",
    "corrected_text",
  ]);

  const sig = "(self, items: AsyncIterable[In]) -> AsyncIterator[Out]";
  const code = [
    [["kw", "class "], ["cls", "ManyToManyStage"], ["pn", "["], ["ty", "In"], ["pn", ", "], ["ty", "Out"], ["pn", "]("], ["ty", "ABC"], ["pn", "):"]],
    [["pn", "    @"], ["dec", "abstractmethod"]],
    [["pl", "    "], ["kw", "def "], ["cls", "process"], ["pn", sig + ":"], ["pn", " ..."]],
    [],
    [],
    [["kw", "class "], ["cls", "OneToOneStage"], ["pn", "["], ["ty", "In"], ["pn", ", "], ["ty", "Out"], ["pn", "]("], ["ty", "ManyToManyStage[In, Out]"], ["pn", "):"]],
    [["pl", "    "], ["kw", "async def "], ["cls", "process"], ["pn", sig + ":"]],
    [["pl", "        "], ["kw", "async for "], ["pl", "item "], ["kw", "in "], ["pl", "items"], ["pn", ":"]],
    [["pl", "            "], ["kw", "yield "], ["pl", "self"], ["pn", "."], ["cls", "process_single"], ["pn", "("], ["pl", "item"], ["pn", ")"]],
    [],
    [["pn", "    @"], ["dec", "abstractmethod"]],
    [["pl", "    "], ["kw", "def "], ["cls", "process_single"], ["pn", "("], ["pl", "self"], ["pn", ", "], ["pl", "item"], ["pn", ": "], ["ty", "In"], ["pn", ") -> "], ["ty", "Out"], ["pn", ":"], ["pn", " ..."]],
  ];

  const morseTable = {
    c: "-.-.", d: "-..", e: ".", i: "..", m: "--", o: "---", r: ".-.", s: "...",
  };

  function morse(word) {
    return [...word].map((letter) => morseTable[letter]);
  }

  return { stages, subscribed, code, morse };
})();
