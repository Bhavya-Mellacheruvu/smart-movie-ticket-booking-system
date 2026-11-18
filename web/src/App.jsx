import { useEffect, useState } from "react";
import { request as call } from "./api.js";
import { money, releaseDateLabel } from "./utils.js";
import CityPicker from "./components/CityPicker.jsx";
import SiteHeader from "./components/SiteHeader.jsx";
import Footer from "./components/Footer.jsx";
import SignInPage from "./pages/SignInPage.jsx";
import DiscoverPage from "./pages/DiscoverPage.jsx";
import BookingPage from "./pages/BookingPage.jsx";
import BookingsPage from "./pages/BookingsPage.jsx";

function App() {
  const [movies, setMovies] = useState([]),
    [cities, setCities] = useState([]),
    [opts, setOpts] = useState(null),
    [bookings, setBookings] = useState([]),
    [filter, setFilter] = useState("All movies"),
    [query, setQuery] = useState(""),
    [selected, setSelected] = useState(null),
    [theatre, setTheatre] = useState(""),
    [date, setDate] = useState(""),
    [time, setTime] = useState(""),
    [seats, setSeats] = useState([]),
    [booked, setBooked] = useState([]),
    [view, setView] = useState("home"),
    [step, setStep] = useState(1),
    [method, setMethod] = useState("simulated-card"),
    [fail, setFail] = useState(false),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false),
    [confirmed, setConfirmed] = useState(null),
    [menu, setMenu] = useState(false),
    [user, setUser] = useState(null),
    [oauthConfigured, setOauthConfigured] = useState(false),
    [city, setCity] = useState(localStorage.getItem("frame_city") || ""),
    [showCityPicker, setShowCityPicker] = useState(false),
    [activeSlide, setActiveSlide] = useState(0);
  useEffect(() => {
    const savedCity = localStorage.getItem("frame_city") || "";
    Promise.all([
      call("/movies"),
      call(
        "/options" +
          (savedCity ? "?city=" + encodeURIComponent(savedCity) : ""),
      ),
      call("/cities"),
      call("/auth/status"),
    ])
      .then(([m, o, c, a]) => {
        setMovies(m);
        setOpts(o);
        setCities(c);
        setUser(a.user);
        setOauthConfigured(a.oauth_configured);
        if (a.user) {
          call("/bookings")
            .then(setBookings)
            .catch(() => {});
          let savedCity = localStorage.getItem("frame_city");
          if (savedCity && !c.some((city) => city.name === savedCity)) {
            localStorage.removeItem("frame_city");
            setCity("");
            savedCity = null;
          }
          if (
            !savedCity &&
            !localStorage.getItem("frame_location_prompted_us_v1")
          ) {
            localStorage.setItem("frame_location_prompted_us_v1", "1");
            setShowCityPicker(true);
          }
        }
      })
      .catch((e) => setNotice(e.message));
    const p = new URLSearchParams(location.search);
    if (p.has("auth_error")) {
      setView("auth");
      setNotice(
        p.get("auth_error") === "oauth_not_configured"
          ? "Google sign-in needs OAuth credentials in the app configuration."
          : "Sign-in could not be completed. Please try again.",
      );
      history.replaceState({}, "", location.pathname);
    }
  }, []);
  const refreshBookings = () =>
    call("/bookings")
      .then(setBookings)
      .catch(() => {});
  const refreshSeats = () => {
    if (selected && theatre && date && time)
      call(
        `/seats?movie=${selected.id}&theatre=${encodeURIComponent(theatre)}&date=${date}&time=${encodeURIComponent(time)}`,
      ).then((x) => {
        setBooked(x.booked);
        setSeats((s) => s.filter((a) => !x.booked.includes(a)));
      });
  };
  useEffect(() => {
    refreshSeats();
  }, [selected, theatre, date, time]);
  const visible = movies.filter(
    (m) =>
      (filter === "All movies" ||
        (filter === "Now showing" && m.status === "now_showing") ||
        (filter === "Coming soon" && m.status === "coming_soon")) &&
      m.title.toLowerCase().includes(query.toLowerCase()),
  );
  const featuredIds = [
    "godzilla-minus-zero",
    "hunger-games-sunrise",
    "focker-in-law",
    "avengers-doomsday",
    "dune-part-three",
    "jumanji-open-world",
  ];
  const featured = featuredIds
    .map((id) => movies.find((m) => m.id === id))
    .filter(Boolean);
  const heroMovie = featured[activeSlide % Math.max(featured.length, 1)] || {
    id: "release-guide",
    title: "New movies for your next night out",
    status: "now_showing",
    tag: "2026 RELEASE GUIDE",
    release_date: "2026-11-06",
    accent: "#4b6570",
    poster: "release-guide",
  };
  useEffect(() => {
    if (featured.length < 2) return;
    const timer = setInterval(
      () => setActiveSlide((i) => (i + 1) % featured.length),
      6500,
    );
    return () => clearInterval(timer);
  }, [featured.length]);
  function startBooking(m) {
    if (!m.booking_open) {
      setNotice(
        `Advance booking opens ${releaseDateLabel(m.booking_opens)}, seven days before release.`,
      );
      return;
    }
    if (!user) {
      sessionStorage.setItem("frame_pending_movie", m.id);
      setView("auth");
      setNotice("Sign in with Google to continue with your booking.");
      window.scrollTo(0, 0);
      return;
    }
    setSelected(m);
    setTheatre(opts?.theatres[0] || "");
    setDate(
      opts?.dates.find((d) => d >= m.release_date) || opts?.dates[0] || "",
    );
    setTime("");
    setSeats([]);
    setStep(1);
    setView("booking");
    setNotice("");
    setConfirmed(null);
    window.scrollTo(0, 0);
  }
  useEffect(() => {
    if (user && opts) {
      const id = sessionStorage.getItem("frame_pending_movie");
      if (id) {
        sessionStorage.removeItem("frame_pending_movie");
        const movie = movies.find((m) => m.id === id);
        if (movie) startBooking(movie);
      }
    }
  }, [user, opts, movies]);
  async function signOut() {
    await call("/auth/logout", { method: "POST" });
    setUser(null);
    setBookings([]);
    setView("home");
  }
  function toggleSeat(s) {
    if (booked.includes(s)) return;
    setSeats((old) =>
      old.includes(s)
        ? old.filter((x) => x !== s)
        : old.length >= 8
          ? old
          : [...old, s],
    );
  }
  async function pay() {
    setBusy(true);
    setNotice("");
    try {
      const b = await call("/bookings", {
        method: "POST",
        body: JSON.stringify({
          movie_id: selected.id,
          theatre,
          show_date: date,
          show_time: time,
          seats,
          payment_method: method,
          simulate_failure: fail,
        }),
      });
      setConfirmed(b);
      setStep(3);
      setBookings((x) => [b, ...x]);
      setView("booking");
    } catch (e) {
      setNotice(e.message);
      refreshSeats();
    } finally {
      setBusy(false);
    }
  }
  async function cancel(id) {
    try {
      await call("/bookings/" + id, { method: "DELETE" });
      setNotice("Booking cancelled. Your seats are available again.");
      refreshBookings();
      refreshSeats();
    } catch (e) {
      setNotice(e.message);
    }
  }
  const goHome = () => {
    setView("home");
    setNotice("");
    window.scrollTo(0, 0);
  };
  function chooseCity(value) {
    localStorage.setItem("frame_city", value);
    setCity(value);
    setShowCityPicker(false);
    call("/options?city=" + encodeURIComponent(value)).then((next) => {
      setOpts(next);
      setTheatre(next.theatres[0] || "");
      setDate("");
      setTime("");
      setSeats([]);
      setStep(1);
      setNotice(
        next.theatres.length
          ? ""
          : `No cinemas are currently listed in ${value}. Try another location.`,
      );
    });
  }
  return (
    <>
      <SiteHeader
        view={view}
        goHome={goHome}
        menu={menu}
        setMenu={setMenu}
        user={user}
        city={city}
        setShowCityPicker={setShowCityPicker}
        signOut={signOut}
        bookings={bookings}
        setView={setView}
        refreshBookings={refreshBookings}
        setNotice={setNotice}
      />
      {view === "auth" && (
        <SignInPage
          goHome={goHome}
          notice={notice}
          setNotice={setNotice}
          oauthConfigured={oauthConfigured}
        />
      )}
      {view === "home" && (
        <DiscoverPage
          heroMovie={heroMovie}
          releaseDateLabel={releaseDateLabel}
          startBooking={startBooking}
          activeSlide={activeSlide}
          featured={featured}
          setActiveSlide={setActiveSlide}
          filter={filter}
          setFilter={setFilter}
          query={query}
          setQuery={setQuery}
          visible={visible}
        />
      )}
      {view === "booking" && (
        <BookingPage
          goHome={goHome}
          confirmed={confirmed}
          selected={selected}
          date={date}
          time={time}
          theatre={theatre}
          city={city}
          seats={seats}
          money={money}
          setView={setView}
          refreshBookings={refreshBookings}
          step={step}
          setStep={setStep}
          opts={opts}
          setTheatre={setTheatre}
          setDate={setDate}
          setSeats={setSeats}
          setTime={setTime}
          booked={booked}
          toggleSeat={toggleSeat}
          method={method}
          setMethod={setMethod}
          fail={fail}
          setFail={setFail}
          busy={busy}
          pay={pay}
          notice={notice}
          setNotice={setNotice}
          releaseDateLabel={releaseDateLabel}
        />
      )}
      {view === "bookings" && (
        <BookingsPage
          notice={notice}
          setNotice={setNotice}
          bookings={bookings}
          goHome={goHome}
          movies={movies}
          money={money}
          cancel={cancel}
        />
      )}
      {view === "bookings" && <Footer />}
      {showCityPicker && user && (
        <CityPicker
          cities={cities}
          onChoose={chooseCity}
          onClose={() => setShowCityPicker(false)}
        />
      )}
    </>
  );
}

export default App;
