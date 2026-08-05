import encoderUrl from "./pcmEncoder.worklet.ts?worker&url";
import { PCM_ENCODER } from "./pcmEncoderName";

export type PcmSink = (chunk: ArrayBuffer) => void;

// A browser hands the microphone to a voice call by default, and every stage of
// that treatment works against a CW tone sitting in the middle of the speech
// band: the suppressor reads a steady tone as noise, the gain control flattens
// the level margin the keying detector thresholds against, and the echo
// canceller subtracts whatever the machine's own speakers are playing — which
// is the signal itself whenever the morse is played back locally.
const CONSTRAINTS: MediaStreamConstraints = {
  audio: {
    echoCancellation: false,
    noiseSuppression: false,
    autoGainControl: false,
    channelCount: 1,
  },
};

const ENCODER_OPTIONS: AudioWorkletNodeOptions = {
  numberOfInputs: 1,
  numberOfOutputs: 1,
  outputChannelCount: [1],
  channelCount: 1,
  channelCountMode: "explicit",
};

// Capture runs in an audio worklet rather than on the main thread: the same page
// paints three charts per frame, and a main-thread processor drops buffers under
// that load. The backend stamps its timeline off the sample count alone, so a
// dropped buffer would not read as a gap but silently shorten every element
// behind it.
export class MicCapture {
  private readonly source: MediaStreamAudioSourceNode;
  private readonly encoder: AudioWorkletNode;

  static async open(): Promise<MicCapture> {
    const stream = await navigator.mediaDevices.getUserMedia(CONSTRAINTS);
    const context = new AudioContext();
    await context.audioWorklet.addModule(encoderUrl);
    return new MicCapture(context, stream);
  }

  private constructor(
    private readonly context: AudioContext,
    private readonly microphone: MediaStream,
  ) {
    this.source = context.createMediaStreamSource(microphone);
    this.encoder = new AudioWorkletNode(context, PCM_ENCODER, ENCODER_OPTIONS);
    // The encoder writes nothing to its output, so this keeps the render graph
    // pulling it without putting the microphone on the speakers.
    this.encoder.connect(context.destination);
  }

  get sampleRate(): number {
    return this.context.sampleRate;
  }

  // Kept apart from construction so the caller gets to announce the sample rate
  // before the first chunk of audio goes out.
  stream(sink: PcmSink): void {
    this.encoder.port.onmessage = (event: MessageEvent<ArrayBuffer>) => sink(event.data);
    this.source.connect(this.encoder);
  }

  async close(): Promise<void> {
    this.encoder.port.onmessage = null;
    this.encoder.disconnect();
    this.source.disconnect();
    this.microphone.getTracks().forEach((track) => track.stop());
    await this.context.close();
  }
}
