export default function SignInPage({
  goHome,
  notice,
  setNotice,
  oauthConfigured,
}) {
  return (
    <main className="auth-page">
      <div className="auth-art">
        <div className="auth-art-orb" />
        <div className="auth-art-arch" />
        <div className="auth-art-copy">
          <span>IMOVIETICKETS ACCOUNT</span>
          <h2>
            Sign in
            <br />
            to <em>iMovieTickets.</em>
          </h2>
          <p>
            View your account
            <br />
            and ticket bookings.
          </p>
        </div>
        <span className="auth-art-index">IMOVIETICKETS ACCOUNT</span>
      </div>
      <section className="auth-panel">
        <button className="back-link auth-back" onClick={goHome}>
          ← <span>Back to films</span>
        </button>
        <div className="auth-content">
          <div className="eyebrow">
            <span className="eyebrow-line" /> ACCOUNT
          </div>
          <h1>Sign in</h1>
          <p className="auth-sub">
            Continue with Google to access your account and bookings. A new
            account is created the first time you sign in.
          </p>
          {notice && <div className="auth-message">{notice}</div>}
          <a className="google-button" href="/auth/google">
            <span className="google-g">G</span>
            <span>Continue with Google</span>
            <b>→</b>
          </a>
          <div className="auth-divider">
            <span />
            SECURE SIGN IN
            <span />
          </div>
          {!oauthConfigured && (
            <p className="auth-setup">Google sign-in is not configured yet.</p>
          )}
          <button className="auth-discover" onClick={goHome}>
            ← Continue browsing films
          </button>
        </div>
        <div className="auth-panel-foot">
          <span>
            IMOVIETICKETS<span className="brand-dot">.</span>
          </span>
          <span>MOVIE TICKET BOOKING</span>
        </div>
      </section>
    </main>
  );
}
