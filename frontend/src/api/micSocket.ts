import { MessageRouter } from "../messages/messageRouter";
import type { PacedIngest } from "../pacing/pacedIngest";
import { storeIngest } from "../pacing/storeIngest";

export type SocketData = ArrayBuffer | string;

export class MicSocketError extends Error {}

function opened(socket: WebSocket): Promise<void> {
  return new Promise((resolve, reject) => {
    socket.addEventListener("open", () => resolve(), { once: true });
    socket.addEventListener("error", () => reject(new MicSocketError(socket.url)), { once: true });
  });
}

// One socket is one decoder session: the backend reads the handshake, streams
// the events it decodes, and is finished when the socket closes.
export class MicSocket {
  private constructor(
    private readonly socket: WebSocket,
    private readonly ingest: PacedIngest,
  ) {}

  static async open(url: string): Promise<MicSocket> {
    const socket = new WebSocket(url);
    const ingest = storeIngest();
    const router = new MessageRouter(ingest.sink);
    socket.onmessage = (event) => router.route(event.data as string);
    await opened(socket);
    const mic = new MicSocket(socket, ingest);
    void mic.commitWhileOpen();
    return mic;
  }

  readonly send = (data: SocketData): void => {
    if (this.socket.readyState === WebSocket.OPEN) this.socket.send(data);
  };

  closed(): Promise<void> {
    return new Promise((resolve) =>
      this.socket.addEventListener("close", () => resolve(), { once: true }),
    );
  }

  close(): void {
    this.socket.close();
  }

  private async commitWhileOpen(): Promise<void> {
    void this.ingest.run();
    await this.closed();
    this.ingest.flush();
    this.ingest.stop();
  }
}
