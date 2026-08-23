import RoleSwitcher from "./RoleSwitcher";


function Header({
  userId,
  onUserChange,
}) {
  return (
    <header className="app-header">

      <div className="brand">
        <div className="brand-mark">
          P
        </div>

        <div>
          <div className="brand-name">
            ParcelPilot
          </div>

          <div className="brand-subtitle">
            Support Console
          </div>
        </div>
      </div>

      <RoleSwitcher
        userId={userId}
        onChange={onUserChange}
      />

    </header>
  );
}

export default Header;