const API_BASE_URL = "http://localhost:8000";

export async function streamChat({
  message,
  userId,
  onEvent,
  onError,
  onDone,
}) {
  try {
    const response = await fetch(
      `${API_BASE_URL}/chat/stream`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-ID": userId,
        },
        body: JSON.stringify({
          message,
        }),
      }
    );

    if (!response.ok) {
      const text = await response.text();

      throw new Error(
        `Chat request failed: ${response.status} ${text}`
      );
    }

    if (!response.body) {
      throw new Error(
        "Streaming response body is unavailable."
      );
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let buffer = "";

    while (true) {
      const { value, done } =
        await reader.read();

      if (done) {
        break;
      }

      buffer += decoder.decode(value, {
        stream: true,
      });

      const events = buffer.split(
        "\n\n"
      );

      buffer = events.pop() ?? "";

      for (const rawEvent of events) {
        const parsed = parseSSEEvent(
          rawEvent
        );

        if (parsed) {
          onEvent?.(parsed);
        }
      }
    }

    // Process any remaining buffered event.
    if (buffer.trim()) {
      const parsed = parseSSEEvent(buffer);

      if (parsed) {
        onEvent?.(parsed);
      }
    }

    onDone?.();
  } catch (error) {
    onError?.(error);
  }
}

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