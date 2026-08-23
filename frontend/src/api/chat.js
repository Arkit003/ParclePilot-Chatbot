const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://localhost:8000";


function parseSSEEvent(rawEvent) {
  const lines = rawEvent.split("\n");

  let eventType = "message";
  let data = "";

  for (const line of lines) {
    if (line.startsWith("event:")) {
      eventType = line
        .slice("event:".length)
        .trim();
    }

    if (line.startsWith("data:")) {
      data += line
        .slice("data:".length)
        .trim();
    }
  }

  if (!data) {
    return null;
  }

  let parsedData;

  try {
    parsedData = JSON.parse(data);
  } catch {
    parsedData = {
      raw: data,
    };
  }

  return {
    type: eventType,
    data: parsedData,
  };
}


export async function streamChat({
  messages,
  userId,
  signal,
  onEvent,
})  {
  const response = await fetch(
  `${API_BASE_URL}/chat/stream`,
  {
    method: "POST",

    headers: {
      "Content-Type": "application/json",
      "X-User-ID": userId,
    },

    body: JSON.stringify({
      messages,
    }),

    signal,
  }
);

  if (!response.ok) {
    let detail = "Chat request failed.";

    try {
      const body = await response.json();

      if (body?.detail) {
        detail = body.detail;
      }
    } catch {
      // Keep default error message.
    }

    throw new Error(
      `${response.status}: ${detail}`
    );
  }

  if (!response.body) {
    throw new Error(
      "Streaming response body is unavailable."
    );
  }

  const reader =
    response.body.getReader();

  const decoder = new TextDecoder();

  let buffer = "";

  while (true) {
    const {
      value,
      done,
    } = await reader.read();

    if (done) {
      break;
    }

    buffer += decoder.decode(
      value,
      {
        stream: true,
      }
    );

    const chunks =
      buffer.split("\n\n");

    buffer =
      chunks.pop() ?? "";

    for (const chunk of chunks) {
      if (!chunk.trim()) {
        continue;
      }

      const event =
        parseSSEEvent(chunk);

      if (event) {
        onEvent?.(event);
      }
    }
  }

  // Flush decoder and remaining buffer.
  buffer += decoder.decode();

  if (buffer.trim()) {
    const event =
      parseSSEEvent(buffer);

    if (event) {
      onEvent?.(event);
    }
  }
}