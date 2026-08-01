# mypy: ignore-errors
# Unveraendert uebernommener Referenz-Generator: bewusst ohne Typannotationen,
# damit der Code 1:1 mit der offiziellen Vorlage vergleichbar bleibt.

import argparse
import sys
import threading
import time
import wave

import numpy as np

# tkinter und sounddevice sind optional: Im reinen CLI-Betrieb (--no-ui) laeuft
# das Tool auch auf Systemen ohne Tk-Bindings bzw. ohne PortAudio/Soundkarte.
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except ImportError:
    tk = None

try:
    import sounddevice as sd
except Exception:
    sd = None

# Standard ITU Morse Code Dictionary
MORSE_DICT = {
    "A": ".-",
    "B": "-...",
    "C": "-.-.",
    "D": "-..",
    "E": ".",
    "F": "..-.",
    "G": "--.",
    "H": "....",
    "I": "..",
    "J": ".---",
    "K": "-.-",
    "L": ".-..",
    "M": "--",
    "N": "-.",
    "O": "---",
    "P": ".--.",
    "Q": "--.-",
    "R": ".-.",
    "S": "...",
    "T": "-",
    "U": "..-",
    "V": "...-",
    "W": ".--",
    "X": "-..-",
    "Y": "-.--",
    "Z": "--..",
    "0": "-----",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
    ".": ".-.-.-",
    ",": "--..--",
    "?": "..--..",
    "/": "-..-.",
    "=": "-...-",
}

# Ab diesem SNR-Wert gilt QRN als abgeschaltet (identisch zum GUI-Verhalten)
QRN_OFF_THRESHOLD = 35

DEFAULT_WPM = 35
DEFAULT_FREQ = 600
DEFAULT_QRN = 20
DEFAULT_QRM = 0.0
DEFAULT_QSB = 0.0
DEFAULT_QSB_RATE = 0.25
DEFAULT_SAMPLE_RATE = 44100
DEFAULT_OUTPUT = "morse.wav"


class AdvancedCWPlayer:
    def __init__(self, sample_rate=DEFAULT_SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.is_playing = False

    def _generate_tone(self, duration, freq, edge_time=0.005):
        t = np.linspace(0, duration, int(self.sample_rate * duration), endpoint=False)
        wave = np.sin(2 * np.pi * freq * t)

        edge_samples = int(self.sample_rate * edge_time)
        if len(wave) > 2 * edge_samples and edge_samples > 0:
            window = np.sin(np.linspace(0, np.pi / 2, edge_samples))
            wave[:edge_samples] *= window
            wave[-edge_samples:] *= window[::-1]

        return wave

    def _generate_silence(self, duration):
        return np.zeros(int(self.sample_rate * duration))

    def text_to_baseband(self, text, wpm, freq):
        """Erzeugt Audio und eine exakte Zeitachse für die GUI-Ausgabe"""
        t_dit = 1.2 / wpm
        t_dah = 3.0 * t_dit
        t_element_space = t_dit
        t_char_space = 3.0 * t_dit
        t_word_space = 7.0 * t_dit

        text = text.upper().replace("\n", " ")
        audio_stream = []
        timings = []
        current_samples = 0

        for char in text:
            if char == " ":
                audio_stream.append(self._generate_silence(t_word_space))
                current_samples += int(self.sample_rate * t_word_space)
                timings.append((" ", current_samples / self.sample_rate))
                continue

            if char not in MORSE_DICT:
                continue

            # Speichere den exakten Start-Zeitpunkt dieses Zeichens
            timings.append((char, current_samples / self.sample_rate))

            elements = MORSE_DICT[char]
            for i, element in enumerate(elements):
                if element == ".":
                    tone = self._generate_tone(t_dit, freq)
                    audio_stream.append(tone)
                    current_samples += len(tone)
                elif element == "-":
                    tone = self._generate_tone(t_dah, freq)
                    audio_stream.append(tone)
                    current_samples += len(tone)

                if i < len(elements) - 1:
                    silence = self._generate_silence(t_element_space)
                    audio_stream.append(silence)
                    current_samples += len(silence)

            silence = self._generate_silence(t_char_space)
            audio_stream.append(silence)
            current_samples += len(silence)

        if not audio_stream:
            return np.array([]), []
        return np.concatenate(audio_stream), timings

    def apply_qsb(self, signal, rate=0.2, depth=0.8):
        t = np.linspace(0, len(signal) / self.sample_rate, len(signal), endpoint=False)
        lfo = (1 - depth) + depth * np.abs(np.sin(2 * np.pi * rate * t))
        return signal * lfo

    def apply_qrm(self, signal, wpm, freq, level):
        if level <= 0:
            return signal
        qrm_text = "CQ DE " + " ".join(["TEST", "VVV", "QRM", "DX", "K"] * 10)
        # Die Zeiten des Störers interessieren uns für die Anzeige nicht, daher '_'
        qrm_signal, _ = self.text_to_baseband(qrm_text, wpm, freq)

        if len(qrm_signal) > len(signal):
            qrm_signal = qrm_signal[: len(signal)]
        else:
            qrm_signal = np.pad(qrm_signal, (0, len(signal) - len(qrm_signal)))

        return signal + (qrm_signal * level)

    def apply_qrn(self, signal, snr_db):
        signal_power = np.mean(signal**2)
        if signal_power == 0:
            return signal
        snr_linear = 10 ** (snr_db / 10)
        noise_power = signal_power / snr_linear
        noise = np.random.normal(0, np.sqrt(noise_power), len(signal))
        return signal + noise

    def render(
        self,
        text,
        wpm,
        freq,
        qsb=DEFAULT_QSB,
        qrm=DEFAULT_QRM,
        qrn=DEFAULT_QRN,
        qsb_rate=DEFAULT_QSB_RATE,
    ):
        """Erzeugt das fertige Signal (inkl. Störungen) und die Timestamps.

        Gemeinsame Render-Pipeline für GUI und CLI.
        """
        audio, timings = self.text_to_baseband(text, wpm, freq)
        if len(audio) == 0:
            return audio, timings

        # Störsignale anwenden
        if qsb > 0:
            audio = self.apply_qsb(audio, rate=qsb_rate, depth=qsb)

        if qrm > 0:
            audio = self.apply_qrm(audio, wpm=wpm + 5, freq=freq + 50, level=qrm)

        if qrn < QRN_OFF_THRESHOLD:
            audio = self.apply_qrn(audio, snr_db=qrn)

        # Audio Normalisierung
        max_amp = np.max(np.abs(audio))
        if max_amp > 0:
            audio = audio / max_amp * 0.8

        return audio, timings

    def save_wav(self, filepath, signal):
        """Schreibt das Signal als 16-Bit Mono PCM WAV-Datei"""
        pcm = np.clip(signal, -1.0, 1.0)
        pcm = (pcm * 32767.0).astype(np.int16)

        with wave.open(filepath, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(pcm.tobytes())

    def stop(self):
        if sd is not None:
            sd.stop()
        self.is_playing = False


def filter_text(content):
    """Entfernt Leerzeilen, Trennlinien und Überschriften aus einem Textblock"""
    filtered_lines = []
    for line in content.split("\n"):
        line = line.strip()
        # Überspringe leere Zeilen
        if not line:
            continue
        # Überspringe Trennlinien
        if line.startswith("---") or line.startswith("==="):
            continue
        # Überspringe spezifische Überschriften
        if "TYPISCHE CW-QSOS" in line or "MORSE-TRAINING" in line:
            continue

        filtered_lines.append(line)

    return "\n".join(filtered_lines)


class CWSimulatorApp:
    def __init__(self, root, settings=None):
        self.root = root
        self.root.title("CW Training Simulator with Live TX")
        self.root.geometry("600x850")

        settings = settings or {}
        self.player = AdvancedCWPlayer(
            sample_rate=settings.get("sample_rate", DEFAULT_SAMPLE_RATE)
        )
        self.qsb_rate = settings.get("qsb_rate", DEFAULT_QSB_RATE)
        self._build_gui(settings)

    def _build_gui(self, settings):
        # --- File Loading Section ---
        file_frame = ttk.LabelFrame(self.root, text="Text Source", padding=10)
        file_frame.pack(fill="x", padx=10, pady=5)

        self.btn_load = ttk.Button(
            file_frame, text="Load Text File", command=self.load_file
        )
        self.btn_load.pack(side="left", padx=5)

        self.lbl_file = ttk.Label(file_frame, text="No file loaded")
        self.lbl_file.pack(side="left", padx=5)

        # --- Filtered Text Display ---
        text_frame = ttk.LabelFrame(
            self.root, text="Current Text (Filtered & Ready)", padding=10
        )
        text_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.text_box = tk.Text(text_frame, height=8, wrap="word", bg="#f0f0f0")
        self.text_box.pack(fill="both", expand=True)

        if settings.get("text"):
            self.text_box.insert("1.0", settings["text"])

        # --- Controls Section ---
        control_frame = ttk.LabelFrame(self.root, text="Signal Parameters", padding=10)
        control_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(control_frame, text="Speed (WPM):").grid(row=0, column=0, sticky="w")
        self.wpm_var = tk.IntVar(value=settings.get("wpm", DEFAULT_WPM))
        ttk.Scale(
            control_frame,
            from_=10,
            to=80,
            variable=self.wpm_var,
            command=self.update_labels,
        ).grid(row=0, column=1, sticky="ew")
        self.lbl_wpm = ttk.Label(control_frame, text=str(self.wpm_var.get()))
        self.lbl_wpm.grid(row=0, column=2)

        ttk.Label(control_frame, text="Pitch (Hz):").grid(row=1, column=0, sticky="w")
        self.freq_var = tk.IntVar(value=settings.get("freq", DEFAULT_FREQ))
        ttk.Scale(
            control_frame,
            from_=400,
            to=1000,
            variable=self.freq_var,
            command=self.update_labels,
        ).grid(row=1, column=1, sticky="ew")
        self.lbl_freq = ttk.Label(control_frame, text=str(self.freq_var.get()))
        self.lbl_freq.grid(row=1, column=2)

        ttk.Label(control_frame, text="QRN SNR (dB):").grid(row=2, column=0, sticky="w")
        self.qrn_var = tk.IntVar(value=settings.get("qrn", DEFAULT_QRN))
        ttk.Scale(
            control_frame,
            from_=0,
            to=40,
            variable=self.qrn_var,
            command=self.update_labels,
        ).grid(row=2, column=1, sticky="ew")
        self.lbl_qrn = ttk.Label(control_frame, text="20 (Clean)")
        self.lbl_qrn.grid(row=2, column=2)

        ttk.Label(control_frame, text="QRM Level:").grid(row=3, column=0, sticky="w")
        self.qrm_var = tk.DoubleVar(value=settings.get("qrm", DEFAULT_QRM))
        ttk.Scale(
            control_frame,
            from_=0.0,
            to=1.0,
            variable=self.qrm_var,
            command=self.update_labels,
        ).grid(row=3, column=1, sticky="ew")
        self.lbl_qrm = ttk.Label(control_frame, text="0.0")
        self.lbl_qrm.grid(row=3, column=2)

        ttk.Label(control_frame, text="QSB Depth:").grid(row=4, column=0, sticky="w")
        self.qsb_var = tk.DoubleVar(value=settings.get("qsb", DEFAULT_QSB))
        ttk.Scale(
            control_frame,
            from_=0.0,
            to=1.0,
            variable=self.qsb_var,
            command=self.update_labels,
        ).grid(row=4, column=1, sticky="ew")
        self.lbl_qsb = ttk.Label(control_frame, text="0.0")
        self.lbl_qsb.grid(row=4, column=2)

        control_frame.columnconfigure(1, weight=1)

        # --- LIVE OUTPUT SECTION ---
        live_frame = ttk.LabelFrame(
            self.root, text="Live TX Output (Synchronized)", padding=10
        )
        live_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.live_output = tk.Text(
            live_frame,
            height=4,
            wrap="word",
            bg="black",
            fg="#00ff00",
            font=("Consolas", 14, "bold"),
        )
        self.live_output.pack(fill="both", expand=True)

        # --- Action Buttons ---
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=10)

        self.btn_play = ttk.Button(btn_frame, text="PLAY", command=self.play_thread)
        self.btn_play.pack(side="left", expand=True, fill="x", padx=5)

        self.btn_stop = ttk.Button(btn_frame, text="STOP", command=self.stop_audio)
        self.btn_stop.pack(side="left", expand=True, fill="x", padx=5)

        self.btn_save = ttk.Button(btn_frame, text="SAVE WAV", command=self.save_thread)
        self.btn_save.pack(side="right", expand=True, fill="x", padx=5)

        self.update_labels()

    def update_labels(self, event=None):
        self.lbl_wpm.config(text=str(self.wpm_var.get()))
        self.lbl_freq.config(text=str(self.freq_var.get()))

        qrn_val = self.qrn_var.get()
        self.lbl_qrn.config(text=f"{qrn_val}" if qrn_val < QRN_OFF_THRESHOLD else "Off")
        self.lbl_qrm.config(text=f"{self.qrm_var.get():.1f}")
        self.lbl_qsb.config(text=f"{self.qsb_var.get():.1f}")

    def load_file(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not filepath:
            return

        self.lbl_file.config(text=filepath.split("/")[-1])

        try:
            with open(filepath, encoding="utf-8") as f:
                content = f.read()

            display_text = filter_text(content)
            self.text_box.delete("1.0", tk.END)
            self.text_box.insert("1.0", display_text)

        except Exception as e:
            messagebox.showerror("Error", f"Could not read file:\n{e}")

    def play_thread(self):
        if self.player.is_playing:
            return

        if sd is None:
            messagebox.showerror(
                "Error", "No audio backend available (sounddevice/PortAudio)."
            )
            return

        text = self.text_box.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "No text to play.")
            return

        thread = threading.Thread(target=self._generate_and_play, args=(text,))
        thread.daemon = True
        thread.start()

    def _render_audio(self, text):
        """Erzeugt das fertige Signal (inkl. Störungen) und die Timestamps"""
        return self.player.render(
            text,
            wpm=self.wpm_var.get(),
            freq=self.freq_var.get(),
            qsb=self.qsb_var.get(),
            qrm=self.qrm_var.get(),
            qrn=self.qrn_var.get(),
            qsb_rate=self.qsb_rate,
        )

    def _generate_and_play(self, text):
        self.btn_play.config(state="disabled")
        self.root.after(0, lambda: self.live_output.delete("1.0", tk.END))

        audio, timings = self._render_audio(text)
        if len(audio) == 0:
            self.btn_play.config(state="normal")
            return

        self.player.is_playing = True

        # Start Playback (non-blocking)
        sd.play(audio, self.player.sample_rate)
        start_time = time.time()

        # Live Text Synchronization
        for char, ts in timings:
            if not self.player.is_playing:
                break

            target_time = start_time + ts
            sleep_time = target_time - time.time()

            if sleep_time > 0:
                time.sleep(sleep_time)

            if not self.player.is_playing:
                break

            # Schreibt das Zeichen in die GUI (Thread-Safe)
            self.root.after(0, self._append_live_text, char)

        # Warte, bis der restliche Audio-Puffer leer ist
        sd.wait()
        self.player.is_playing = False
        self.btn_play.config(state="normal")

    def save_thread(self):
        if self.player.is_playing:
            return

        text = self.text_box.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "No text to save.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".wav",
            initialfile="morse.wav",
            filetypes=[("WAV Files", "*.wav"), ("All Files", "*.*")],
        )
        if not filepath:
            return

        thread = threading.Thread(target=self._generate_and_save, args=(text, filepath))
        thread.daemon = True
        thread.start()

    def _generate_and_save(self, text, filepath):
        self.btn_save.config(state="disabled")

        try:
            audio, _ = self._render_audio(text)
            if len(audio) == 0:
                self.root.after(
                    0,
                    lambda: messagebox.showwarning(
                        "Warning", "No playable characters in text."
                    ),
                )
                return

            self.player.save_wav(filepath, audio)
            name = filepath.split("/")[-1]
            self.root.after(
                0, lambda: messagebox.showinfo("Saved", f"WAV file saved:\n{name}")
            )

        except Exception as error:
            # In eine lokale Variable binden: 'error' ist nach dem except-Block
            # geloescht, das Lambda laeuft aber erst spaeter im Tk-Mainloop.
            message = f"Could not save file:\n{error}"
            self.root.after(0, lambda: messagebox.showerror("Error", message))

        finally:
            self.btn_save.config(state="normal")

    def _append_live_text(self, char):
        self.live_output.insert(tk.END, char)
        self.live_output.see(tk.END)  # Auto-Scroll

    def stop_audio(self):
        self.player.stop()
        self.btn_play.config(state="normal")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="morse",
        description=(
            "CW/Morse Training Simulator - GUI oder reines CLI (--no-ui) für Pipelines."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Beispiele:\n"
            "  python main.py\n"
            "      Startet die GUI mit Standardwerten (unverändertes Verhalten).\n"
            "  python main.py --text 'CQ CQ DE DL1ABC K' --wpm 25\n"
            "      Startet die GUI mit vorbelegtem Text und Tempo.\n"
            "  python main.py --no-ui --text 'CQ DE DL1ABC K' -o out.wav\n"
            "      Schreibt nur die WAV-Datei, keine GUI, kein Audio-Device nötig.\n"
            "  echo 'CQ TEST' | python main.py --no-ui --qrn 10 --qsb 0.5\n"
            "      Text kann alternativ über stdin kommen.\n"
        ),
    )

    parser.add_argument(
        "--text",
        metavar="TEXT",
        help="Zu sendender Text (direkt als Wert, kein Dateiname). "
        "Ohne diesen Parameter wird stdin gelesen, falls es keine TTY ist.",
    )
    parser.add_argument(
        "--wpm",
        type=int,
        default=DEFAULT_WPM,
        metavar="N",
        help=f"Gebetempo in Wörtern pro Minute (Default: {DEFAULT_WPM})",
    )
    parser.add_argument(
        "--freq",
        "--pitch",
        dest="freq",
        type=int,
        default=DEFAULT_FREQ,
        metavar="HZ",
        help=f"Tonhöhe in Hz (Default: {DEFAULT_FREQ})",
    )
    parser.add_argument(
        "--qrn",
        type=float,
        default=DEFAULT_QRN,
        metavar="DB",
        help=f"Rauschabstand SNR in dB; ab {QRN_OFF_THRESHOLD} ist QRN aus "
        f"(Default: {DEFAULT_QRN})",
    )
    parser.add_argument(
        "--qrm",
        type=float,
        default=DEFAULT_QRM,
        metavar="LEVEL",
        help=f"Pegel der Störstation, 0.0-1.0 (Default: {DEFAULT_QRM})",
    )
    parser.add_argument(
        "--qsb",
        type=float,
        default=DEFAULT_QSB,
        metavar="DEPTH",
        help=f"Schwund-Tiefe, 0.0-1.0 (Default: {DEFAULT_QSB})",
    )
    parser.add_argument(
        "--qsb-rate",
        type=float,
        default=DEFAULT_QSB_RATE,
        metavar="HZ",
        help=f"Schwund-Frequenz in Hz (Default: {DEFAULT_QSB_RATE})",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=DEFAULT_SAMPLE_RATE,
        metavar="HZ",
        help=f"Abtastrate in Hz (Default: {DEFAULT_SAMPLE_RATE})",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT,
        metavar="PFAD",
        help=f"Zieldatei für die WAV-Ausgabe bei --no-ui (Default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--filter-text",
        action="store_true",
        help="Wendet denselben Filter wie der GUI-Dateiimport an "
        "(entfernt Leerzeilen, Trennlinien, Überschriften)",
    )
    parser.add_argument(
        "--no-ui",
        action="store_true",
        help="Keine GUI: erzeugt ausschließlich die WAV-Datei und beendet sich",
    )

    return parser


def validate_args(parser, args):
    if args.wpm <= 0:
        parser.error("--wpm muss größer als 0 sein")
    if args.freq <= 0:
        parser.error("--freq muss größer als 0 sein")
    if args.sample_rate <= 0:
        parser.error("--sample-rate muss größer als 0 sein")
    if not 0.0 <= args.qrm <= 1.0:
        parser.error("--qrm muss zwischen 0.0 und 1.0 liegen")
    if not 0.0 <= args.qsb <= 1.0:
        parser.error("--qsb muss zwischen 0.0 und 1.0 liegen")
    if args.qsb_rate <= 0:
        parser.error("--qsb-rate muss größer als 0 sein")


def resolve_text(args, allow_stdin=True):
    """Text kommt aus --text oder, falls nicht angegeben, aus stdin (Pipe).

    Im GUI-Modus wird stdin bewusst nicht gelesen, damit der Start nie blockiert.
    """
    if args.text is not None:
        text = args.text
    elif allow_stdin and not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        return None

    if args.filter_text:
        text = filter_text(text)

    return text.strip()


def run_cli(args):
    text = resolve_text(args)
    if not text:
        print(
            "Fehler: kein Text. --text TEXT angeben oder Text über stdin pipen.",
            file=sys.stderr,
        )
        return 2

    player = AdvancedCWPlayer(sample_rate=args.sample_rate)
    audio, _ = player.render(
        text,
        wpm=args.wpm,
        freq=args.freq,
        qsb=args.qsb,
        qrm=args.qrm,
        qrn=args.qrn,
        qsb_rate=args.qsb_rate,
    )

    if len(audio) == 0:
        print("Fehler: Text enthält keine sendbaren Zeichen.", file=sys.stderr)
        return 1

    try:
        player.save_wav(args.output, audio)
    except OSError as e:
        print(
            f"Fehler: WAV-Datei konnte nicht geschrieben werden: {e}", file=sys.stderr
        )
        return 1

    print(args.output)
    return 0


def run_gui(args):
    if tk is None:
        print(
            "Fehler: tkinter ist nicht verfügbar. "
            "Für den CLI-Betrieb --no-ui verwenden.",
            file=sys.stderr,
        )
        return 1

    settings = {
        "text": resolve_text(args, allow_stdin=False),
        "wpm": args.wpm,
        "freq": args.freq,
        "qrn": int(args.qrn),
        "qrm": args.qrm,
        "qsb": args.qsb,
        "qsb_rate": args.qsb_rate,
        "sample_rate": args.sample_rate,
    }

    root = tk.Tk()
    CWSimulatorApp(root, settings)
    root.mainloop()
    return 0


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(parser, args)

    if args.no_ui:
        return run_cli(args)
    return run_gui(args)


if __name__ == "__main__":
    sys.exit(main())
