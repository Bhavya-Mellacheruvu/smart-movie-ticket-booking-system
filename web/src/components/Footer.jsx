export default function Footer() {
  return (
    <footer className="footer">
      <button
        className="brand"
        onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
      >
        <span className="brand-icon">
          i<span>·</span>
        </span>
        iMovieTickets<span className="brand-dot">.</span>
      </button>
      <span className="footer-copy">
        MOVIE TICKET BOOKING. <b>© IMOVIETICKETS 2026</b>
      </span>
      <span className="footer-demo">
        ✳ SIMULATED EXPERIENCE · NO REAL PAYMENTS
      </span>
    </footer>
  );
}
