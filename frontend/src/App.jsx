import { useState } from "react";

import ChatWindow from "./components/ChatWindow";
import RoleSwitcher from "./components/RoleSwitcher";
import "./styles/app.css";


function App() {
  const [userId, setUserId] =
    useState("customer-northstar");

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>ParcelPilot</h1>
          <p>AI Support Agent</p>
        </div>

        <RoleSwitcher
          userId={userId}
          onChange={setUserId}
        />
      </header>

      <main>
        <ChatWindow
          key={userId}
          userId={userId}
        />
      </main>
    </div>
  );
}

export default App;