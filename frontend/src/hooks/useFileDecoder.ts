import { useState } from "react";
import { UPLOAD_URL } from "../api/endpoints";
import { MessageRouter } from "../messages/messageRouter";
import { NdjsonStream } from "../messages/ndjsonStream";
import { storeSink } from "../messages/storeSink";
import { useStore } from "../store";

function uploadBody(file: File): FormData {
  const body = new FormData();
  body.append("file", file);
  return body;
}

async function render(events: ReadableStream<Uint8Array>): Promise<void> {
  const router = new MessageRouter(storeSink());
  for await (const line of new NdjsonStream(events).lines()) router.route(line);
}

export function useFileDecoder() {
  const [status, setStatus] = useState<string | null>(null);

  const decode = async (file: File): Promise<void> => {
    setStatus(`Decoding ${file.name}…`);
    useStore.getState().clearDecoded();
    try {
      const response = await fetch(UPLOAD_URL, { method: "POST", body: uploadBody(file) });
      if (!response.ok || !response.body) {
        setStatus(`Decoding failed (${response.status})`);
        return;
      }
      await render(response.body);
      setStatus(`Decoded ${file.name}`);
    } catch {
      setStatus(`Could not reach the decoder`);
    }
  };

  return { status, decode };
}
