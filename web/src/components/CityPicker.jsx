import { useState } from "react";

export default function CityPicker({ cities, onChoose, onClose }) {
  const [query, setQuery] = useState(""),
    [showAll, setShowAll] = useState(false),
    [locating, setLocating] = useState(false),
    [message, setMessage] = useState("");
  const list = cities.filter((c) =>
    c.name.toLowerCase().includes(query.trim().toLowerCase()),
  );
  function detect() {
    if (!navigator.geolocation) {
      setMessage(
        "Location detection is unavailable in this browser. Search for your city instead.",
      );
      return;
    }
    setLocating(true);
    setMessage("");
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        setLocating(false);
        const distance = (c) => {
          const rad = (x) => (x * Math.PI) / 180,
            dy = rad(c.lat - coords.latitude),
            dx = rad(c.lon - coords.longitude),
            a =
              Math.sin(dy / 2) ** 2 +
              Math.cos(rad(coords.latitude)) *
                Math.cos(rad(c.lat)) *
                Math.sin(dx / 2) ** 2;
          return 6371 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        };
        const nearest = [...cities].sort(
          (a, b) => distance(a) - distance(b),
        )[0];
        if (distance(nearest) < 150) onChoose(nearest.name);
        else
          setMessage(
            "We couldn’t match your location to a supported city. Search or choose one below.",
          );
      },
      () => {
        setLocating(false);
        setMessage(
          "Location access wasn’t available. Search for your city instead.",
        );
      },
      { timeout: 10000, maximumAge: 300000 },
    );
  }
  return (
    <div
      className="city-overlay"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <section
        className="city-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="location-title"
      >
        <button
          className="city-close"
          aria-label="Close city picker"
          onClick={onClose}
        >
          ×
        </button>
        <div className="city-search">
          <span>⌕</span>
          <input
            id="city-search"
            aria-label="Search for a city"
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search for your city"
          />
          <kbd>ESC</kbd>
        </div>
        <button
          className="detect-location"
          onClick={detect}
          disabled={locating}
        >
          <span>◎</span>
          {locating ? "Finding nearby city…" : "Detect my location"}
        </button>
        {message && (
          <p className="city-message" role="status">
            {message}
          </p>
        )}
        <div className="city-divider" />
        <h2 id="location-title">{query ? "Cities" : "Popular Cities"}</h2>
        <div className="city-grid">
          {list.slice(0, showAll || query ? list.length : 10).map((c, i) => (
            <button
              className="city-option"
              key={c.name}
              onClick={() => onChoose(c.name)}
            >
              <span className="city-landmark" aria-hidden="true">
                <svg viewBox="0 0 48 42">
                  <path
                    d={
                      i % 4 === 0
                        ? "M5 36h38M9 34V18h30v16M7 18l17-10 17 10M15 34V23h6v11m6 0V23h6v11"
                        : i % 4 === 1
                          ? "M6 36h36M11 34V16h26v18M9 16h30l-3-5H12zM17 34V23a7 7 0 0 1 14 0v11M22 12V7h4v5"
                          : i % 4 === 2
                            ? "M5 36h38M9 34V19l15-9 15 9v15M15 34V22h18v12M21 22v12m6-12v12M21 10V6h6v4"
                            : "M5 36h38M10 34V17h28v17M8 17l16-9 16 9M18 34V22h12v12M21 25h6"
                    }
                  />
                </svg>
              </span>
              <span>{c.name}</span>
            </button>
          ))}
        </div>
        {!query && (
          <button className="view-cities" onClick={() => setShowAll((x) => !x)}>
            {showAll ? "Show popular cities" : "View all cities"}{" "}
            <span>{showAll ? "↑" : "↓"}</span>
          </button>
        )}
        {query && list.length === 0 && (
          <p className="city-empty">No matching cities. Try another search.</p>
        )}
        <p className="city-footnote">
          Optional — choose a location now or later.
        </p>
        <button className="city-skip" onClick={onClose}>
          Maybe later
        </button>
      </section>
    </div>
  );
}
