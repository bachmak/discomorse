import { useRef, useState } from "react";
import { UPLOAD_URL } from "../api/endpoints";
import { MessageRouter } from "../messages/messageRouter";
import { NdjsonStream } from "../messages/ndjsonStream";
import { storeSink } from "../messages/storeSink";
import { useStore } from "../store";

export interface FileDecoder {
  status: string | null;
  source: File | null;
  decode: (file: File) => Promise<void>;
  restart: () => Promise<void>;
}

function uploadBody(file: File): FormData {
  const body = new FormData();
  body.append("file", file);
  return body;
}

async function render(events: ReadableStream<Uint8Array>): Promise<void> {
  const router = new MessageRouter(storeSink());
  for await (const line of new NdjsonStream(events).lines()) router.route(line);
}

export function useFileDecoder(): FileDecoder {
  const [status, setStatus] = useState<string | null>(null);
  const [source, setSource] = useState<File | null>(null);
  const runRef = useRef<AbortController | null>(null);

  // Replaying means abandoning whatever is still streaming, so the store is
  // never fed by two runs of the same file at once.
  const begin = (file: File): AbortSignal => {
    runRef.current?.abort();
    runRef.current = new AbortController();
    useStore.getState().reset();
    setStatus(`Decoding ${file.name}…`);
    return runRef.current.signal;
  };

  const play = async (file: File): Promise<void> => {
    const signal = begin(file);
    try {
      const body = uploadBody(file);
      const response = await fetch(UPLOAD_URL, { method: "POST", body, signal });
      if (!response.ok || !response.body) {
        setStatus(`Decoding failed (${response.status})`);
        return;
      }
      await render(response.body);
      setStatus(`Decoded ${file.name}`);
    } catch {
      if (!signal.aborted) setStatus("Could not reach the decoder");
    }
  };

  const decode = async (file: File): Promise<void> => {
    setSource(file);
    await play(file);
  };

  const restart = async (): Promise<void> => {
    if (source) await play(source);
  };

  return { status, source, decode, restart };
}
