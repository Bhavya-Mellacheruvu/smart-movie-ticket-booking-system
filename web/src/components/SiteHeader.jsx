import Avatar from "./Avatar.jsx";

export default function SiteHeader({
  view,
  goHome,
  menu,
  setMenu,
  user,
  city,
  setShowCityPicker,
  signOut,
  bookings,
  setView,
  refreshBookings,
  setNotice,
}) {
  return (
    <header className={view === "home" ? "topbar topbar-cinema" : "topbar"}>
      <button className="brand" onClick={goHome}>
        <span className="brand-icon">
          i<span>·</span>
        </span>
        iMovieTickets<span className="brand-dot">.</span>
      </button>
      <nav className={menu ? "nav open" : "nav"}>
        <button
          className={view === "home" ? "nav-link active" : "nav-link"}
          onClick={goHome}
        >
          Discover
        </button>
        {user && (
          <button
            className={view === "bookings" ? "nav-link active" : "nav-link"}
            onClick={() => {
              setView("bookings");
              refreshBookings();
              setMenu(false);
            }}
          >
            My bookings
            {bookings.length > 0 && (
              <span className="nav-count">{bookings.length}</span>
            )}
          </button>
        )}
      </nav>
      <div className="nav-right">
        {user && (
          <button className="city-nav" onClick={() => setShowCityPicker(true)}>
            <span>⌖</span>
            {city || "Select location"}
          </button>
        )}
        {user ? (
          <>
            <button
              className="account-chip"
              onClick={() => setView("bookings")}
            >
              <Avatar user={user} />
              <span>{user.name}</span>
            </button>
            <button className="auth-nav" onClick={signOut}>
              Sign out
            </button>
          </>
        ) : (
          <button
            className="auth-nav"
            onClick={() => {
              setView("auth");
              setNotice("");
            }}
          >
            Sign in
          </button>
        )}
        <button className="menu-btn" onClick={() => setMenu(!menu)}>
          ☰
        </button>
      </div>
    </header>
  );
}
