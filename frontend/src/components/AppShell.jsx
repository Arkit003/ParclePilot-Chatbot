import Header from "./Header";


function AppShell({
  userId,
  onUserChange,
  children,
}) {
  return (
    <div className="app-shell">

      <Header
        userId={userId}
        onUserChange={onUserChange}
      />

      <main className="app-main">
        {children}
      </main>

    </div>
  );
}

export default AppShell;