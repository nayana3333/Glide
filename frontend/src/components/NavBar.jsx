import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

const LINKS = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/forecast", label: "Forecast" },
  { to: "/buffer", label: "Buffer" },
  { to: "/income", label: "Income Log" },
  { to: "/insights", label: "Insights" },
];

export default function NavBar() {
  const { user, logout } = useAuth();

  return (
    <nav className="navbar">
      <div className="navbar-brand">Glide</div>
      <div className="navbar-links">
        {LINKS.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) => "navbar-link" + (isActive ? " active" : "")}
          >
            {link.label}
          </NavLink>
        ))}
      </div>
      <div className="navbar-user">
        <span>{user?.name}</span>
        <button className="btn btn-ghost" onClick={logout}>
          Log out
        </button>
      </div>
    </nav>
  );
}
