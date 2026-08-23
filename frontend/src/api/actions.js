const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://localhost:8000";


export async function executeAction({
  confirmationId,
  confirmed,
  userId,
}) {
  if (!confirmationId) {
    throw new Error(
      "Missing confirmation ID."
    );
  }

  const response = await fetch(
    `${API_BASE_URL}/actions/${encodeURIComponent(
      confirmationId
    )}/execute?confirmed=${confirmed}`,
    {
      method: "POST",

      headers: {
        "X-User-ID": userId,
      },
    }
  );


  let body = null;

  try {
    body = await response.json();
  } catch {
    // Response may not contain JSON.
  }


  if (!response.ok) {
    throw new Error(
      body?.detail ||
        "Unable to process the action."
    );
  }


  return body;
}