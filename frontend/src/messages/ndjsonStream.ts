const LINE_BREAK = "\n";

export class NdjsonStream {
  constructor(private readonly body: ReadableStream<Uint8Array>) {}

  async *lines(): AsyncGenerator<string> {
    let partial = "";
    for await (const text of this.chunks()) {
      const lines = (partial + text).split(LINE_BREAK);
      partial = lines.pop() ?? "";
      yield* lines.filter((line) => line.length > 0);
    }
    if (partial.length > 0) yield partial;
  }

  private async *chunks(): AsyncGenerator<string> {
    const decoder = new TextDecoder();
    const reader = this.body.getReader();
    try {
      for (;;) {
        const chunk = await reader.read();
        if (chunk.done) {
          yield decoder.decode();
          return;
        }
        yield decoder.decode(chunk.value, { stream: true });
      }
    } finally {
      reader.releaseLock();
    }
  }
}
