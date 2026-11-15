import Poster from "../components/Poster.jsx";
import Footer from "../components/Footer.jsx";

export default function DiscoverPage(props) {
  const {
    heroMovie,
    releaseDateLabel,
    startBooking,
    activeSlide,
    featured,
    setActiveSlide,
    filter,
    setFilter,
    query,
    setQuery,
    visible,
  } = props;
  return (
    <div className="discover-shell">
      <main>
        <section
          className="hero movie-carousel"
          style={{ "--hero-accent": heroMovie.accent || "#50616d" }}
        >
          <div className="hero-copy">
            <div className="eyebrow">
              <span className="eyebrow-line" />{" "}
              {heroMovie.status === "coming_soon"
                ? "COMING SOON"
                : "NOW SHOWING"}{" "}
              <span className="hero-release-date">
                · {releaseDateLabel(heroMovie.release_date)}
              </span>
            </div>
            <h1 className="movie-headline">{heroMovie.title}</h1>
            <p className="hero-sub">
              {heroMovie.status === "coming_soon"
                ? "Coming to U.S. theaters soon."
                : "Explore showtimes and book tickets."}
            </p>
            {heroMovie.booking_open ? (
              <button
                className="hero-cta"
                onClick={() => startBooking(heroMovie)}
              >
                {heroMovie.status === "coming_soon"
                  ? "Pre-book tickets"
                  : "Get tickets"}{" "}
                <span>↗</span>
              </button>
            ) : (
              <button
                className="hero-cta"
                onClick={() =>
                  document
                    .getElementById("films")
                    .scrollIntoView({ behavior: "smooth" })
                }
              >
                Opens {releaseDateLabel(heroMovie.booking_opens)} <span>↓</span>
              </button>
            )}
            <div className="hero-foot">
              <span className="release-note">2026 U.S. RELEASE GUIDE</span>
              <span>Release dates may change</span>
            </div>
          </div>
          <div className="hero-visual">
            <div className="hero-image">
              <Poster movie={heroMovie} large />
              <div className="hero-caption">
                FEATURED FILM{" "}
                <span>
                  {String(activeSlide + 1).padStart(2, "0")} /{" "}
                  {String(Math.max(featured.length, 1)).padStart(2, "0")}
                </span>
              </div>
            </div>
            <div className="hero-side-note">
              2026 RELEASES <span>·</span> U.S. THEATERS
            </div>
            <div className="hero-slider-controls">
              <button
                aria-label="Previous movie"
                onClick={() =>
                  setActiveSlide(
                    (i) =>
                      (i - 1 + Math.max(featured.length, 1)) %
                      Math.max(featured.length, 1),
                  )
                }
              >
                ‹
              </button>
              <div className="hero-slider-dots">
                {featured.map((m, i) => (
                  <button
                    key={m.id}
                    aria-label={"Show " + m.title}
                    aria-current={i === activeSlide}
                    onClick={() => setActiveSlide(i)}
                  />
                ))}
              </div>
              <button
                aria-label="Next movie"
                onClick={() =>
                  setActiveSlide((i) => (i + 1) % Math.max(featured.length, 1))
                }
              >
                ›
              </button>
            </div>
          </div>
        </section>
        <section className="film-section" id="films">
          <div className="section-head">
            <div>
              <div className="eyebrow">
                <span className="eyebrow-line" /> MOVIES
              </div>
              <h2>
                Browse <em>movies.</em>
              </h2>
            </div>
            <div className="section-note">
              Recent releases and upcoming
              <br />
              U.S. theatrical movies. <span>↘</span>
            </div>
          </div>
          <div className="film-controls">
            <div className="filters">
              {["All movies", "Now showing", "Coming soon"].map((x) => (
                <button
                  key={x}
                  className={filter === x ? "filter active" : "filter"}
                  onClick={() => setFilter(x)}
                >
                  {x}
                </button>
              ))}
            </div>
            <label className="search">
              <span>⌕</span>
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Find a film"
              />
              <kbd>⌘ K</kbd>
            </label>
          </div>
          <div className="movie-grid">
            {visible.map((m, i) => (
              <article
                key={m.id}
                className="movie-card"
                style={{ "--delay": `${i * 65}ms` }}
              >
                <button
                  className="poster-button"
                  disabled={!m.booking_open}
                  onClick={() => startBooking(m)}
                  aria-label={
                    !m.booking_open
                      ? m.title +
                        " advance booking opens " +
                        releaseDateLabel(m.booking_opens)
                      : "Book " + m.title
                  }
                >
                  <Poster movie={m} />
                  <span className="poster-arrow">↗</span>
                </button>
                <div className="movie-info">
                  <div>
                    <h3>{m.title}</h3>
                    <p>
                      {m.status === "coming_soon"
                        ? "Coming soon"
                        : "Now showing"}
                    </p>
                  </div>
                </div>
                <div className="movie-bottom">
                  <span>
                    U.S. RELEASE <i /> {releaseDateLabel(m.release_date)}
                  </span>
                  <button
                    disabled={!m.booking_open}
                    onClick={() => startBooking(m)}
                  >
                    {m.booking_open
                      ? m.status === "coming_soon"
                        ? "Pre-book"
                        : "Get tickets"
                      : `Opens ${releaseDateLabel(m.booking_opens)}`}{" "}
                    <span>↗</span>
                  </button>
                </div>
              </article>
            ))}
          </div>
          {visible.length === 0 && (
            <div className="empty">
              No films match that search. Try another title or genre.
            </div>
          )}
        </section>
      </main>
      <Footer />
    </div>
  );
}
