import Poster from "../components/Poster.jsx";

export default function BookingsPage(props) {
  const { notice, setNotice, bookings, goHome, movies, money, cancel } = props;
  return (
    <main className="bookings-page">
      <div className="eyebrow">
        <span className="eyebrow-line" /> MY BOOKINGS
      </div>
      <h1>My bookings</h1>
      <p className="booking-intro">View and manage your tickets.</p>
      {notice && (
        <div className="notice-bar">
          {notice}
          <button onClick={() => setNotice("")}>×</button>
        </div>
      )}
      {bookings.length === 0 ? (
        <div className="empty-bookings">
          <span>✳</span>
          <h2>No bookings yet.</h2>
          <p>Browse movies to book a ticket.</p>
          <button className="primary-btn" onClick={goHome}>
            Browse movies <span>↗</span>
          </button>
        </div>
      ) : (
        <div className="booking-list">
          {bookings.map((b) => (
            <article className="booking-card" key={b.id}>
              <div className="booking-card-art">
                <Poster
                  movie={
                    movies.find((m) => m.id === b.movie_id) || {
                      poster: "midnight",
                      title: b.movie,
                      tag: "IMOVIETICKETS",
                      genre: "Film",
                      year: 2025,
                    }
                  }
                />
              </div>
              <div className="booking-card-content">
                <div className="ticket-brand">
                  IMOVIETICKETS <span>· {b.id}</span>
                </div>
                <h2>{b.movie}</h2>
                <p>{b.theatre}</p>
                <div className="booking-card-meta">
                  <span>
                    <small>SHOWTIME</small>
                    {new Date(b.show_date + "T12:00:00").toLocaleDateString(
                      "en-US",
                      { weekday: "short", month: "short", day: "numeric" },
                    )}{" "}
                    · {b.show_time}
                  </span>
                  <span>
                    <small>SEATS</small>
                    {b.seats.join(", ")}
                  </span>
                  <span>
                    <small>TOTAL · DEMO</small>
                    {money(b.total)}
                  </span>
                </div>
              </div>
              <div className="booking-card-actions">
                <span className="confirmed-pill">
                  <i /> CONFIRMED
                </span>
                <button className="cancel-btn" onClick={() => cancel(b.id)}>
                  Cancel booking
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </main>
  );
}
