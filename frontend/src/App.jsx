
import { useState } from "react";
import "./App.css";

import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Organizatons from "./pages/Organizatons.jsx";
import Projects from "./pages/Projects.jsx";
import Queues from "./pages/Queues.jsx";
import Jobs from "./pages/Jobs.jsx";
import Workers from "./pages/Workers.jsx";
import Scheduled_jobs from "./pages/Scheduled_jobs.jsx";

function App() {
  // ============================================================
  // AUTHENTICATION
  // ============================================================

  const [loggedIn, setLoggedIn] = useState(
    () => localStorage.getItem("access_token") !== null
  );

  // ============================================================
  // CURRENT PAGE
  // ============================================================

  const [activePage, setActivePage] = useState("Dashboard");

  // ============================================================
  // SIDEBAR MENU
  // ============================================================

  const menuItems = [
    {
      name: "Dashboard",
      icon: "▦",
    },
    {
      name: "Organizations",
      icon: "▤",
    },
    {
      name: "Projects",
      icon: "▣",
    },
    {
      name: "Queues",
      icon: "☷",
    },
    {
      name: "Jobs",
      icon: "⚡",
    },
    {
      name: "Workers",
      icon: "◉",
    },
    {
      name: "Scheduled Jobs",
      icon: "◷",
    },
  ];

  // ============================================================
  // PAGE RENDERING
  // ============================================================

  const renderPage = () => {
    switch (activePage) {
      case "Dashboard":
        return <Dashboard />;

      case "Organizations":
        return <Organizatons />;

      case "Projects":
        return <Projects />;

      case "Queues":
        return <Queues />;

      case "Jobs":
        return <Jobs />;

      case "Workers":
        return <Workers />;

      case "Scheduled Jobs":
        return <Scheduled_jobs />;

      default:
        return <Dashboard />;
    }
  };

  // ============================================================
  // LOGIN
  // ============================================================

  const handleLogin = () => {
    setLoggedIn(true);
    setActivePage("Dashboard");
  };

  // ============================================================
  // LOGOUT
  // ============================================================

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("user_email");

    setLoggedIn(false);
    setActivePage("Dashboard");
  };

  // ============================================================
  // LOGIN PAGE
  // ============================================================

  if (!loggedIn) {
    return <Login onLogin={handleLogin} />;
  }

  // ============================================================
  // USER INFORMATION
  // ============================================================

  const userEmail =
    localStorage.getItem("user_email") || "User";

  // Get first letter for avatar
  const avatarLetter =
    userEmail.charAt(0).toUpperCase();

  // ============================================================
  // MAIN APPLICATION
  // ============================================================

  return (
    <div className="app">

      {/* ======================================================
          SIDEBAR
      ====================================================== */}

      <aside className="sidebar">

        {/* BRAND */}

        <div className="brand">

          <div className="brand-icon">
            JS
          </div>

          <div>
            <h2>JobScheduler</h2>

            <span>
              Distributed Platform
            </span>
          </div>

        </div>

        {/* NAVIGATION */}

        <nav className="navigation">

          {menuItems.map((item) => (
            <button
              key={item.name}
              type="button"
              className={`nav-item ${
                activePage === item.name
                  ? "active"
                  : ""
              }`}
              onClick={() =>
                setActivePage(item.name)
              }
            >

              <span className="nav-icon">
                {item.icon}
              </span>

              <span>
                {item.name}
              </span>

            </button>
          ))}

        </nav>

        {/* SYSTEM STATUS */}

        <div className="sidebar-bottom">

          <div className="system-status">

            <span className="status-dot"></span>

            <div>

              <strong>
                System Online
              </strong>

              <small>
                All services operational
              </small>

            </div>

          </div>

        </div>

      </aside>

      {/* ======================================================
          MAIN CONTENT
      ====================================================== */}

      <main className="main">

        {/* HEADER */}

        <header className="topbar">

          <div>

            <h1>
              {activePage}
            </h1>

            <p>
              Distributed Job Scheduler
            </p>

          </div>

          {/* USER SECTION */}

          <div className="user-section">

            <div className="notification">
              🔔
            </div>

            <div className="user-avatar">
              {avatarLetter}
            </div>

            <div className="user-info">

              <strong>
                {userEmail}
              </strong>

              <small>
                User
              </small>

            </div>

            <button
              type="button"
              className="logout-button"
              onClick={logout}
            >
              Logout
            </button>

          </div>

        </header>

        {/* PAGE CONTENT */}

        <div className="page-content">
          {renderPage()}
        </div>

      </main>

    </div>
  );
}

export default App;

