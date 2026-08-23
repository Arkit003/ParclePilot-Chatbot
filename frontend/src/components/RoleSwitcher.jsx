const USERS = [
  {
    id: "customer-northstar",
    label: "Northstar Customer",
  },
  {
    id: "customer-lumenworks",
    label: "LumenWorks Customer",
  },
  {
    id: "customer-beacon",
    label: "Beacon Customer",
  },
  {
    id: "customer-axis",
    label: "Axis Customer",
  },
  {
    id: "rohit",
    label: "Rohit · Support",
  },
  {
    id: "maya",
    label: "Maya · Support",
  },
  {
    id: "manager",
    label: "Manager",
  },
];


function RoleSwitcher({
  userId,
  onChange,
}) {
  return (
    <select
      className="role-switcher"
      value={userId}
      onChange={(event) =>
        onChange(event.target.value)
      }
    >
      {USERS.map((user) => (
        <option
          key={user.id}
          value={user.id}
        >
          {user.label}
        </option>
      ))}
    </select>
  );
}

export default RoleSwitcher;