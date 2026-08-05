PRES.data = (() => {
  const interfaces = [
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

  const notes = {
    sa: [
      "Reassembles chunks into whole frames",
      "Hann window, fixed hop per frame",
      "FFT magnitude per frequency bin",
      "Stamps each frame at its centre time",
    ],
    sl: [
      "Holds one band, fixed by config",
      "Drops every bin outside min..max Hz",
      "Keeps out-of-band noise off the peak",
    ],
    cs: [
      "Reads the loudest bin per spectrum",
      "Searches while the peak wanders",
      "Locks a tone that repeats long enough",
      "A rival must outlast it to take over",
    ],
    ne: [
      "Looks at every bin of one spectrum",
      "Takes a low percentile as the floor",
      "Robust: most bins carry only noise",
    ],
    kd: [
      "Follows the noise floor with an EMA",
      "Rises fast, falls slow",
      "Thresholds sit a factor above it",
      "Hysteresis FSM: on high, off low",
    ],
    kb: [
      "A change must hold before it counts",
      "Separate rise and fall delays",
      "Pending state buffers the samples",
      "Too brief: rewritten to the old side",
    ],
    td: [
      "Cuts the stream into on/off spans",
      "An EMA tracks the current dit length",
      "Classifier chain claims each span",
      "Dits, dahs and gaps, measured in dits",
    ],
    sd: [
      "An FSM gathers elements into codes",
      "Gaps close a character or a word",
      "The ITU table reads the code as text",
      "Same elements always spell the same",
    ],
    tc: [
      "Buffers characters into a run",
      "Scores every way to cut it up",
      "Word prices come from a lexicon",
      "Heard gaps are evidence, not orders",
      "Emits a word once its cut is settled",
    ],
  };

  const glyphs = {
    sa: { in: "wave", out: "spectrum" },
    sl: { in: "spectrum", out: "band" },
    cs: { in: "band", out: "peak" },
    ne: { in: "band", out: "noise" },
    kd: { in: "mixed", out: "pulses" },
    kb: { in: "pulses", out: "clean" },
    td: { in: "clean", out: "morse" },
    sd: { in: "morse", out: "letters" },
    tc: { in: "letters", out: "text" },
  };

  const stages = interfaces.map((stage) => ({
    ...stage,
    notes: notes[stage.id],
    glyphs: glyphs[stage.id],
  }));
  const byId = Object.fromEntries(stages.map((stage) => [stage.id, stage]));

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

  return { stages, byId, subscribed, code, morse };
})();
