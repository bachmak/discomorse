export interface TransportState {
  readonly fileName: string | null;
  readonly playing: boolean;
  readonly currentTime: number;
  readonly duration: number;
}

export function idleTransport(): TransportState {
  return { fileName: null, playing: false, currentTime: 0, duration: 0 };
}
