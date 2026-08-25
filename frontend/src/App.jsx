import { useState } from "react";

import AppShell from "./components/AppShell";
import ChatWindow from "./components/ChatWindow";

import "./styles/globals.css";
import "./styles/shell.css";
import "./styles/chat.css";


function App() {
  const [userId, setUserId] =
    useState("customer-northstar");

  return (
    <AppShell
      userId={userId}
      onUserChange={setUserId}
    >
      <div className="service-notice">
        <strong>Service notice:</strong>{" "}
        The backend is hosted on Render's free tier
        and may sleep after periods of inactivity.
        The first request after inactivity can take a
        few minutes while the service wakes up and
        initializes the embedding model. Subsequent
        requests should normally complete much faster.
      </div>

      <ChatWindow userId={userId} />
    </AppShell>
  );
}

export default App;