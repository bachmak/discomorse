# Course Assignment: Intelligent Morse Code Decoder

**Institution:** TH Köln – University of Applied Sciences  
**Faculty:** Faculty of Computer Science and Engineering  
**Instructor:** Prof. Dr. Peter Kern

---

## Introduction

Morse code remains a fundamental communication method in amateur radio and maritime distress signaling. Modern digital signal processing (DSP) and machine learning (ML) allow for the automation of decoding even under extremely challenging conditions. The objective of this assignment is to develop a robust, real-time Morse Code Decoder in Python.

---

## Core Requirements

The software must be implemented using a **strictly Object-Oriented Programming (OOP)** approach. Students are expected to design a modular architecture that separates signal acquisition, digital processing, decoding logic, and visualization.

### Functional Specifications

- **Live Audio Streaming:** The system must be capable of processing an audio stream in real-time (e.g., captured from a WebSDR via virtual audio cable or microphone input), as well as audio files such as mp3.

- **Signal Visualization:** The application must provide a live visual representation of the signal. Implement at least one of the following:
  - Time-domain signal (Oscilloscope view).
  - Frequency-domain representation (FFT Spectrum).
  - Waterfall display (Spectrogram).

- **Digital Signal Filtering:** Implement initial filtering stages (e.g., Bandpass, Lowpass, or adaptive noise reduction) to isolate the CW (Continuous Wave) signal and improve the Signal-to-Noise Ratio (SNR).

- **User Interface:** A dedicated window must display the decoded text in real-time as it is being processed.

---

## Robustness and Adaptivity

A primary challenge of this project is the handling of imperfect human-sent or interference-prone signals. The decoder must demonstrate:

- **Variable Speed Detection:** Automatic recognition and adaptation to different transmission speeds (Words Per Minute – WPM).

- **Noise Handling:** The ability to decode "noisy" signals where signal levels fluctuate or static interference is present.

- **Timing Flexibility:** Robust detection of Morse elements (Dits and Dahs) including compensation for variations in inter-character and word spacing.

---

## Intelligent Decoding Layer

The decoder shall include an intelligent interpretation layer:

- **Probabilistic Correction:** Implement a model that uses probability (e.g., Hidden Markov Models or N-grams) to fill gaps or correct likely errors in the character stream.

- **Training Data:** The model should be trained on typical Morse code conversations, including standard prosigns (e.g., CQ, K, AR, SK) and common abbreviations used in amateur radio (QSO patterns).

- **Contextual Awareness:** The system should leverage statistical distributions of language to improve accuracy during poor signal conditions.

---

## Resources and References

Students are encouraged to have a look on the following:

- **Audio Training Data:** *Morse Code Ninja* (https://morsecode.ninja/resources/index.html) provides an extensive library of audio files for various speeds and signal conditions.

- **Reference Tools:** Examine the behavior of mobile applications like *Morse Expert* and *GGMorse* for UI/UX and decoding performance benchmarks.

---

## Deliverables

1. A fully documented Python codebase following clean code and OOP principles.
2. A short demonstration/screencast of the decoder working with an audio file.

---

*Good luck with the implementation!*
