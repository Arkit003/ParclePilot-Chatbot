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
      <ChatWindow userId={userId} />
    </AppShell>
  );
}

export default App;