import Poster from "../components/Poster.jsx";

export default function BookingPage(props) {
  const {
    goHome,
    confirmed,
    selected,
    date,
    time,
    theatre,
    city,
    seats,
    money,
    setView,
    refreshBookings,
    step,
    setStep,
    opts,
    setTheatre,
    setDate,
    setSeats,
    setTime,
    booked,
    toggleSeat,
    method,
    setMethod,
    fail,
    setFail,
    busy,
    pay,
    notice,
    setNotice,
    releaseDateLabel,
  } = props;
  return (
    <main className="flow-page">
      <button className="back-link" onClick={goHome}>
        ← <span>Back to films</span>
      </button>
      {confirmed ? (
        <section className="confirmation">
          <div className="confirm-icon">✓</div>
          <div className="eyebrow">
            <span className="eyebrow-line" /> BOOKING CONFIRMED
          </div>
          <h1>
            Booking <em>confirmed.</em>
          </h1>
          <p className="confirm-sub">
            Your booking is confirmed. Your ticket details are below.
          </p>
          <div className="ticket">
            <div className="ticket-poster">
              <Poster movie={selected} large />
            </div>
            <div className="ticket-details">
              <div className="ticket-brand">
                IMOVIETICKETS <span>· ADMIT ONE</span>
              </div>
              <h2>{selected.title}</h2>
              <p>{theatre}</p>
              <div className="ticket-rule" />
              <div className="ticket-grid">
                <div>
                  <small>DATE & TIME</small>
                  <strong>
                    {new Date(date + "T12:00:00").toLocaleDateString("en-US", {
                      weekday: "short",
                      month: "short",
                      day: "numeric",
                    })}{" "}
                    · {time}
                  </strong>
                </div>
                <div>
                  <small>SEATS</small>
                  <strong>{confirmed.seats.join(", ")}</strong>
                </div>
                <div>
                  <small>BOOKING REFERENCE</small>
                  <strong className="ref">{confirmed.id}</strong>
                </div>
                <div>
                  <small>PAID</small>
                  <strong>{money(confirmed.total)} · SIMULATED</strong>
                </div>
              </div>
              <div className="ticket-barcode">▌▌ ▌ ▌▌▌ ▌▌ ▌ ▌▌▌ ▌▌▌ ▌ ▌▌</div>
            </div>
          </div>
          <div className="confirmation-actions">
            <button className="primary-btn" onClick={goHome}>
              Discover more films <span>↗</span>
            </button>
            <button
              className="text-btn"
              onClick={() => {
                setView("bookings");
                refreshBookings();
              }}
            >
              View my bookings
            </button>
          </div>
          <p className="sim-note">
            This is a demo booking. No real payment was processed.
          </p>
        </section>
      ) : (
        <div className="booking-layout">
          <div className="booking-main">
            <div className="eyebrow">
              <span className="eyebrow-line" /> BOOK TICKETS
            </div>
            <h1 className="flow-title">
              Book <em>tickets.</em>
            </h1>
            <div className="steps">
              <div className={step >= 1 ? "step active" : ""}>
                <b>01</b>
                <span>Showtime</span>
              </div>
              <i />
              <div className={step >= 2 ? "step active" : ""}>
                <b>02</b>
                <span>Your seats</span>
              </div>
              <i />
              <div className={step >= 3 ? "step active" : ""}>
                <b>03</b>
                <span>Checkout</span>
              </div>
            </div>
            {step === 1 && (
              <>
                <h2 className="form-heading">Choose your screening</h2>
                <div className="form-field">
                  <label>CINEMA</label>
                  <div className="select-wrap">
                    <select
                      value={theatre}
                      disabled={!opts?.theatres.length}
                      onChange={(e) => {
                        setTheatre(e.target.value);
                        setSeats([]);
                      }}
                    >
                      <option value="" disabled>
                        {opts?.theatres.length
                          ? "Choose a cinema"
                          : "No cinemas in this location"}
                      </option>
                      {opts?.theatres.map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))}
                    </select>
                    <span>⌄</span>
                  </div>
                  {!opts?.theatres.length && (
                    <p className="notice-bar cinema-unavailable">
                      No sample cinemas are available in {city || "this location"}.
                      Try another location to continue booking.
                    </p>
                  )}
                </div>
                <div className="form-field">
                  <label>DATE</label>
                  <div className="date-options">
                    {opts?.dates
                      .filter((d) => d >= selected.release_date)
                      .map((d, i) => (
                        <button
                          key={d}
                          className={date === d ? "date-option chosen" : ""}
                          onClick={() => {
                            setDate(d);
                            setSeats([]);
                          }}
                        >
                          <div
                            style={{
                              display: "flex",
                              flexDirection: "column",
                              alignItems: "center",
                              justifyContent: "center",
                              gap: "3px",
                              whiteSpace: "nowrap",
                              fontFamily: "DM Sans, sans-serif",
                            }}
                          >
                            <small
                              style={{
                                fontFamily: "DM Sans, sans-serif",
                                color: date === d ? "#ffc0b5" : "#242329",
                              }}
                            >
                              {d === opts?.dates[0]
                                ? "TODAY"
                                : new Date(d + "T12:00:00")
                                    .toLocaleDateString("en-US", {
                                      weekday: "short",
                                    })
                                    .toUpperCase()}
                            </small>
                            <b
                              style={{
                                fontFamily: "DM Sans, sans-serif",
                                color: date === d ? "#ffffff" : "#242329",
                              }}
                            >
                              {new Date(d + "T12:00:00").getDate()}
                            </b>
                            <span
                              style={{
                                fontFamily: "DM Sans, sans-serif",
                                color: date === d ? "#ffc0b5" : "#242329",
                              }}
                            >
                              {new Date(d + "T12:00:00")
                                .toLocaleDateString("en-US", {
                                  month: "short",
                                })
                                .toUpperCase()}
                            </span>
                          </div>
                        </button>
                      ))}
                  </div>
                </div>
                <div className="form-field">
                  <label>
                    SHOWTIME <span>· ALL TIMES LOCAL</span>
                  </label>
                  <div className="time-options">
                    {opts?.times.map((t, i) => (
                      <button
                        key={t}
                        className={time === t ? "time-option chosen" : ""}
                        onClick={() => {
                          setTime(t);
                          setSeats([]);
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            flexDirection: "column",
                            alignItems: "center",
                            justifyContent: "center",
                            gap: "3px",
                            whiteSpace: "nowrap",
                            fontFamily: "DM Sans, sans-serif",
                          }}
                        >
                          <span
                            style={{
                              fontFamily: "DM Sans, sans-serif",
                              color: time === t ? "#ffffff" : "#242329",
                            }}
                          >
                            {t}
                          </span>
                          <small
                            style={{
                              fontFamily: "DM Sans, sans-serif",
                              color: time === t ? "#ffc0b5" : "#242329",
                            }}
                          >
                            {i === 0
                              ? "STANDARD"
                              : i === 3
                                ? "POPULAR"
                                : "STANDARD"}
                          </small>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
                <div className="booking-actions">
                  <button
                    className="primary-btn"
                    disabled={!theatre || !date || !time}
                    onClick={() => setStep(2)}
                  >
                    Choose your seats <span>→</span>
                  </button>
                  <span className="quiet">
                    Tickets from {money(opts?.seat_price || 14)}
                  </span>
                </div>
              </>
            )}
            {step === 2 && (
              <>
                <h2 className="form-heading">
                  Pick your seats{" "}
                  <span className="sub-count">{seats.length}/8 SELECTED</span>
                </h2>
                <div className="seat-legend">
                  <span>
                    <i className="legend-seat available" />
                    Available
                  </span>
                  <span>
                    <i className="legend-seat selected-seat" />
                    Selected
                  </span>
                  <span>
                    <i className="legend-seat booked-seat" />
                    Taken
                  </span>
                </div>
                <div className="screen">
                  <span>SCREEN</span>
                </div>
                <div className="seat-map">
                  {"ABCDEFGH".split("").map((row) => (
                    <div className="seat-row" key={row}>
                      <span className="row-label">{row}</span>
                      {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => {
                        const s = row + n;
                        return (
                          <button
                            aria-label={"Seat " + s}
                            title={
                              "Seat " +
                              s +
                              (booked.includes(s) ? " (taken)" : "")
                            }
                            disabled={booked.includes(s)}
                            key={s}
                            onClick={() => toggleSeat(s)}
                            className={`seat ${booked.includes(s) ? "taken" : seats.includes(s) ? "picked" : ""}`}
                          />
                        );
                      })}
                      <span className="row-label">{row}</span>
                    </div>
                  ))}
                </div>
                <div className="seat-note">
                  Seats are held once your simulated booking is confirmed.
                </div>
                <div className="booking-actions">
                  <button
                    className="primary-btn"
                    disabled={!seats.length}
                    onClick={() => setStep(3)}
                  >
                    Continue to checkout <span>→</span>
                  </button>
                  <button className="text-btn" onClick={() => setStep(1)}>
                    ← Change screening
                  </button>
                </div>
              </>
            )}
            {step === 3 && (
              <>
                <h2 className="form-heading">One last thing</h2>
                <div className="checkout-summary">
                  <Poster movie={selected} />
                  <div>
                    <b>{selected.title}</b>
                    <span>{theatre}</span>
                    <span>
                      {new Date(date + "T12:00:00").toLocaleDateString(
                        "en-US",
                        { weekday: "short", month: "short", day: "numeric" },
                      )}{" "}
                      · {time}
                    </span>
                    <span>Seats {seats.join(", ")}</span>
                  </div>
                </div>
                <div className="payment-label">SIMULATED PAYMENT METHOD</div>
                <button
                  className={
                    method === "simulated-card"
                      ? "payment-option chosen"
                      : "payment-option"
                  }
                  onClick={() => setMethod("simulated-card")}
                >
                  <span className="pay-icon">▰</span>
                  <span>
                    <b>Demo card</b>
                    <small>Instant simulated approval</small>
                  </span>
                  <i />
                </button>
                <button
                  className={
                    method === "at-counter"
                      ? "payment-option chosen"
                      : "payment-option"
                  }
                  onClick={() => setMethod("at-counter")}
                >
                  <span className="pay-icon">⌂</span>
                  <span>
                    <b>Pay at the cinema</b>
                    <small>Simulated pay-at-counter booking</small>
                  </span>
                  <i />
                </button>
                <label className="failure-toggle">
                  <input
                    type="checkbox"
                    checked={fail}
                    onChange={(e) => setFail(e.target.checked)}
                  />
                  <span>Simulate a declined payment</span>
                  <small>For demo purposes only</small>
                </label>
                <div className="booking-actions">
                  <button
                    className="primary-btn"
                    disabled={busy || !theatre || !date || !time || !seats.length}
                    onClick={pay}
                  >
                    {busy ? "Confirming…" : "Confirm booking"} <span>→</span>
                  </button>
                  <button className="text-btn" onClick={() => setStep(2)}>
                    ← Change seats
                  </button>
                </div>
                <p className="sim-note inline">
                  No card details needed. This is a simulated transaction.
                </p>
              </>
            )}
          </div>
          <aside className="booking-aside">
            <div className="aside-poster">
              <Poster movie={selected} large />
            </div>
            <div className="aside-label">BOOKING SUMMARY</div>
            <h3>{selected.title}</h3>
            <p>
              {selected.tag} <i /> {releaseDateLabel(selected.release_date)}
            </p>
            <div className="aside-rule" />
            <div className="aside-detail">
              <span>CINEMA</span>
              <b>{theatre}</b>
            </div>
            <div className="aside-detail">
              <span>SCREENING</span>
              <b>{time || "Choose a showtime"}</b>
            </div>
            <div className="aside-detail">
              <span>SEATS</span>
              <b>{seats.length ? seats.join(", ") : "Not selected"}</b>
            </div>
            <div className="aside-rule" />
            <div className="total-row">
              <span>
                {seats.length} {seats.length === 1 ? "ticket" : "tickets"}
              </span>
              <b>{money(seats.length * 14)}</b>
            </div>
            <div className="aside-foot">
              ✳ <span>Booking details</span>
            </div>
          </aside>
          {notice && (
            <div className="toast" role="alert">
              {notice}
              <button onClick={() => setNotice("")}>×</button>
            </div>
          )}
        </div>
      )}
    </main>
  );
}
