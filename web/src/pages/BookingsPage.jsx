import { useEffect, useState } from "react";
import Poster from "../components/Poster.jsx";
import { isShowtimePast } from "../utils.js";

export default function BookingsPage(props) {
  const [currentInstant, setCurrentInstant] = useState(() => new Date());
  const [pendingCancellation, setPendingCancellation] = useState(null);
  useEffect(() => {
    const timer = setInterval(() => setCurrentInstant(new Date()), 30_000);
    return () => clearInterval(timer);
  }, []);
  useEffect(() => {
    if (!pendingCancellation) return undefined;
    const handleKeyDown = (event) => {
      if (event.key === "Escape") setPendingCancellation(null);
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [pendingCancellation]);
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
      {pendingCancellation && (
        <div
          className="cancel-confirm-overlay"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              setPendingCancellation(null);
            }
          }}
        >
          <section
            className="cancel-confirm-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="cancel-confirm-title"
            aria-describedby="cancel-confirm-description"
          >
            <span className="eyebrow">
              <span className="eyebrow-line" /> CANCEL BOOKING
            </span>
            <h2 id="cancel-confirm-title">Cancel this ticket?</h2>
            <p id="cancel-confirm-description">
              Your seats will be released and this booking will be cancelled.
              Are you sure you want to continue?
            </p>
            <div className="cancel-confirm-actions">
              <button
                className="text-btn"
                onClick={() => setPendingCancellation(null)}
              >
                No, keep booking
              </button>
              <button
                className="primary-btn"
                onClick={async () => {
                  const bookingId = pendingCancellation.id;
                  setPendingCancellation(null);
                  await cancel(bookingId);
                }}
              >
                Yes, cancel ticket
              </button>
            </div>
          </section>
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
          {bookings.map((b) => {
            const showtimePast = isShowtimePast(
              b.show_date,
              b.show_time,
              b.timezone,
              currentInstant,
            );
            // The showtime is the source of truth for the label. Older API
            // responses may not include can_cancel, and stale flags must
            // not mark a future screening as past.
            const canCancel = !showtimePast && b.can_cancel !== false;
            return (
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
                {canCancel ? (
                  <button
                    className="cancel-btn"
                    onClick={() => setPendingCancellation(b)}
                  >
                    Cancel booking
                  </button>
                ) : (
                  <span className="past-ticket-pill">PAST SHOW</span>
                )}
              </div>
              </article>
            );
          })}
        </div>
      )}
    </main>
  );
}
