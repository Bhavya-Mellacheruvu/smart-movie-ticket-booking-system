"""iMovieTickets: a local movie ticket booking prototype."""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from pathlib import Path

from authlib.integrations.flask_client import OAuth
from flask import (
    Flask,
    jsonify,
    redirect,
    request,
    send_from_directory,
    session,
    url_for,
)

from services import (
    BookingValidationError,
    booking_options,
    movie_catalog,
    validate_booking,
)

ROOT = Path(__file__).resolve().parent


def load_local_config():
    config_file = ROOT / ".env"
    if config_file.exists():
        for line in config_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


load_local_config()
DB_PATH = Path(os.environ.get("MOVIE_DB", ROOT / "movie_bookings.sqlite3"))
app = Flask(
    __name__,
    static_folder=str(ROOT / "web" / "dist"),
    static_url_path="",
)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY", "local-development-key-change-before-deploy"
)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1",
)
oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

SHOWTIMES = ["10:30 AM", "1:15 PM", "4:00 PM", "6:45 PM", "9:20 PM"]


@contextmanager
def connect():
    """Open a database connection and always commit/rollback and close it."""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    with connect() as db:
        db.executescript(
            """
        CREATE TABLE IF NOT EXISTS movies (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            release_date TEXT,
            year INTEGER,
            poster TEXT,
            accent TEXT,
            genre TEXT,
            language TEXT,
            rating TEXT,
            duration TEXT,
            tag TEXT,
            description TEXT,
            is_listed INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS cities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS theatres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            city_id INTEGER NOT NULL REFERENCES cities(id),
            active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS screens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            theatre_id INTEGER NOT NULL REFERENCES theatres(id),
            name TEXT NOT NULL,
            seat_rows INTEGER NOT NULL DEFAULT 8,
            seats_per_row INTEGER NOT NULL DEFAULT 10,
            active INTEGER NOT NULL DEFAULT 1,
            UNIQUE(theatre_id,name)
        );
        CREATE TABLE IF NOT EXISTS screenings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id TEXT NOT NULL REFERENCES movies(id),
            show_date TEXT NOT NULL,
            show_time TEXT NOT NULL,
            screen_id INTEGER NOT NULL REFERENCES screens(id),
            UNIQUE(movie_id, screen_id, show_date, show_time)
        );
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY, google_sub TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL, name TEXT NOT NULL, picture TEXT,
            created_at TEXT NOT NULL
        );
        """
        )

        if db.execute("SELECT COUNT(*) FROM movies").fetchone()[0] == 0:
            seed = json.loads((ROOT / "movie_catalog_seed.json").read_text())
            db.executemany(
                """INSERT INTO movies
                   (id,title,release_date,year,poster,accent,genre,language,rating,duration,tag,description,is_listed)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                [
                    (
                        movie["id"],
                        movie["title"],
                        movie.get("release_date"),
                        movie.get("year"),
                        movie.get("poster"),
                        movie.get("accent"),
                        movie.get("genre"),
                        movie.get("language"),
                        movie.get("rating"),
                        movie.get("duration"),
                        movie.get("tag"),
                        movie.get("description"),
                        movie.get("is_listed", 1),
                    )
                    for movie in seed
                ],
            )

        _seed_cities_and_theatres(db)

        screening_columns = {
            row["name"] for row in db.execute("PRAGMA table_info(screenings)")
        }
        if "screen_id" not in screening_columns:
            db.execute(
                "ALTER TABLE screenings ADD COLUMN screen_id INTEGER REFERENCES screens(id)"
            )
        if "theatre" in screening_columns:
            for screening in db.execute(
                "SELECT id,theatre FROM screenings WHERE screen_id IS NULL"
            ).fetchall():
                screen_id = _default_screen_id(db, screening["theatre"])
                db.execute(
                    "UPDATE screenings SET screen_id=? WHERE id=?",
                    (screen_id, screening["id"]),
                )

        booking_columns = {
            row["name"] for row in db.execute("PRAGMA table_info(bookings)")
        }
        if not booking_columns:
            _create_booking_tables(db)
        elif "screening_id" not in booking_columns:
            _migrate_legacy_bookings(db, booking_columns)
        else:
            seat_columns = {
                row["name"] for row in db.execute("PRAGMA table_info(booking_seats)")
            }
            if seat_columns and "is_reserved" not in seat_columns:
                _migrate_booking_seats_table(db)
            else:
                _create_booking_seats_table(db)
        _normalize_screenings_table(db)
        db.execute(
            "CREATE INDEX IF NOT EXISTS idx_bookings_user_status ON bookings(user_id,status,created_at)"
        )


def _create_booking_tables(db):
    db.execute(
        """CREATE TABLE IF NOT EXISTS bookings (
        id TEXT PRIMARY KEY,
        screening_id INTEGER NOT NULL REFERENCES screenings(id),
        total INTEGER NOT NULL,
        payment_status TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'confirmed',
        created_at TEXT NOT NULL,
        user_id TEXT REFERENCES users(id),
        UNIQUE(id,screening_id)
    )"""
    )
    _create_booking_seats_table(db)


def _create_booking_seats_table(db):
    db.execute(
        """CREATE TABLE IF NOT EXISTS booking_seats (
        screening_id INTEGER NOT NULL REFERENCES screenings(id),
        booking_id TEXT NOT NULL,
        seat TEXT NOT NULL,
        is_reserved INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY(booking_id, seat),
        FOREIGN KEY(booking_id,screening_id) REFERENCES bookings(id,screening_id) ON DELETE CASCADE
    )"""
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_booking_seats_booking ON booking_seats(booking_id)"
    )
    db.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_booking_seats_reserved ON booking_seats(screening_id,seat) WHERE is_reserved=1"
    )


def _migrate_booking_seats_table(db):
    """Retain released seat history while enforcing uniqueness for reserved seats."""
    db.execute(
        """CREATE TABLE booking_seats_v2 (
        screening_id INTEGER NOT NULL REFERENCES screenings(id),
        booking_id TEXT NOT NULL,
        seat TEXT NOT NULL,
        is_reserved INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY(booking_id, seat),
        FOREIGN KEY(booking_id,screening_id) REFERENCES bookings(id,screening_id) ON DELETE CASCADE
    )"""
    )
    db.execute(
        """INSERT INTO booking_seats_v2(screening_id,booking_id,seat,is_reserved)
        SELECT screening_id,booking_id,seat,1 FROM booking_seats"""
    )
    db.execute("DROP TABLE booking_seats")
    db.execute("ALTER TABLE booking_seats_v2 RENAME TO booking_seats")
    _create_booking_seats_table(db)


def _get_or_create_screening(db, movie_id, theatre, show_date, show_time):
    screen_id = _default_screen_id(db, theatre)
    columns = {row["name"] for row in db.execute("PRAGMA table_info(screenings)")}
    if "theatre" in columns:
        db.execute(
            "INSERT OR IGNORE INTO screenings(movie_id,theatre,show_date,show_time,screen_id) VALUES(?,?,?,?,?)",
            (movie_id, theatre, show_date, show_time, screen_id),
        )
        row = db.execute(
            "SELECT id FROM screenings WHERE movie_id=? AND theatre=? AND show_date=? AND show_time=?",
            (movie_id, theatre, show_date, show_time),
        ).fetchone()
    else:
        db.execute(
            "INSERT OR IGNORE INTO screenings(movie_id,show_date,show_time,screen_id) VALUES(?,?,?,?)",
            (movie_id, show_date, show_time, screen_id),
        )
        row = db.execute(
            "SELECT id FROM screenings WHERE movie_id=? AND screen_id=? AND show_date=? AND show_time=?",
            (movie_id, screen_id, show_date, show_time),
        ).fetchone()
    return row["id"]


def _seed_cities_and_theatres(db):
    if db.execute("SELECT COUNT(*) FROM cities").fetchone()[0] == 0:
        cities = json.loads((ROOT / "city_seed.json").read_text())
        db.executemany(
            "INSERT INTO cities(name,latitude,longitude) VALUES(?,?,?)",
            [(city["name"], city["latitude"], city["longitude"]) for city in cities],
        )
    if db.execute("SELECT COUNT(*) FROM theatres").fetchone()[0] == 0:
        venues = json.loads((ROOT / "theatre_seed.json").read_text())
        for venue in venues:
            city = db.execute(
                "SELECT id FROM cities WHERE name=?", (venue["city"],)
            ).fetchone()
            db.execute(
                "INSERT INTO theatres(name,city_id) VALUES(?,?)",
                (venue["name"], city["id"]),
            )
            theatre_id = db.execute(
                "SELECT id FROM theatres WHERE name=?", (venue["name"],)
            ).fetchone()["id"]
            db.execute(
                "INSERT INTO screens(theatre_id,name,seat_rows,seats_per_row) VALUES(?,?,8,10)",
                (theatre_id, venue["screen_name"]),
            )
    else:
        # Add a default screen for theatres introduced after the initial seed.
        rows = db.execute("SELECT id FROM theatres WHERE active=1").fetchall()
        for row in rows:
            exists = db.execute(
                "SELECT 1 FROM screens WHERE theatre_id=? AND active=1", (row["id"],)
            ).fetchone()
            if not exists:
                db.execute(
                    "INSERT INTO screens(theatre_id,name) VALUES(?,?)",
                    (row["id"], "Screen 1"),
                )


def _default_screen_id(db, theatre_name):
    screen = db.execute(
        """SELECT s.id FROM screens s JOIN theatres t ON t.id=s.theatre_id
           WHERE t.name=? AND s.active=1 AND t.active=1 ORDER BY s.id LIMIT 1""",
        (theatre_name,),
    ).fetchone()
    if not screen:
        raise ValueError(f"No active screen is configured for theatre: {theatre_name}")
    return screen["id"]


def _normalize_screenings_table(db):
    """Replace the old theatre-name screening key with a screen foreign key."""
    columns = {row["name"] for row in db.execute("PRAGMA table_info(screenings)")}
    if "theatre" not in columns:
        return

    db.execute("DROP TABLE IF EXISTS screenings_v2")
    db.execute(
        """CREATE TABLE screenings_v2 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        movie_id TEXT NOT NULL REFERENCES movies(id),
        show_date TEXT NOT NULL,
        show_time TEXT NOT NULL,
        screen_id INTEGER NOT NULL REFERENCES screens(id),
        UNIQUE(movie_id,screen_id,show_date,show_time)
    )"""
    )
    db.execute(
        """INSERT INTO screenings_v2(id,movie_id,show_date,show_time,screen_id)
        SELECT id,movie_id,show_date,show_time,screen_id FROM screenings"""
    )
    db.execute(
        """CREATE TABLE bookings_v2 (
        id TEXT PRIMARY KEY,
        screening_id INTEGER NOT NULL REFERENCES screenings_v2(id),
        total INTEGER NOT NULL,
        payment_status TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'confirmed',
        created_at TEXT NOT NULL,
        user_id TEXT REFERENCES users(id),
        UNIQUE(id,screening_id)
    )"""
    )
    db.execute(
        """INSERT INTO bookings_v2(id,screening_id,total,payment_status,status,created_at,user_id)
        SELECT id,screening_id,total,payment_status,status,created_at,user_id FROM bookings"""
    )
    db.execute(
        """CREATE TABLE booking_seats_v2 (
        screening_id INTEGER NOT NULL REFERENCES screenings_v2(id),
        booking_id TEXT NOT NULL,
        seat TEXT NOT NULL,
        is_reserved INTEGER NOT NULL DEFAULT 1,
        PRIMARY KEY(booking_id,seat),
        FOREIGN KEY(booking_id,screening_id) REFERENCES bookings_v2(id,screening_id) ON DELETE CASCADE
    )"""
    )
    db.execute(
        """INSERT INTO booking_seats_v2(screening_id,booking_id,seat,is_reserved)
        SELECT screening_id,booking_id,seat,is_reserved FROM booking_seats"""
    )
    db.execute("DROP TABLE booking_seats")
    db.execute("DROP TABLE bookings")
    db.execute("DROP TABLE screenings")
    db.execute("ALTER TABLE screenings_v2 RENAME TO screenings")
    db.execute("ALTER TABLE bookings_v2 RENAME TO bookings")
    db.execute("ALTER TABLE booking_seats_v2 RENAME TO booking_seats")
    _create_booking_seats_table(db)


def _migrate_legacy_bookings(db, booking_columns):
    """Move the original denormalized bookings and held seats into related tables."""
    if "user_id" not in booking_columns:
        db.execute("ALTER TABLE bookings ADD COLUMN user_id TEXT REFERENCES users(id)")
    old_rows = db.execute("SELECT * FROM bookings").fetchall()
    db.execute("DROP TABLE IF EXISTS held_seats")
    db.execute("ALTER TABLE bookings RENAME TO bookings_legacy")
    _create_booking_tables(db)

    for old in old_rows:
        movie_id = old["movie_id"]
        if not db.execute("SELECT 1 FROM movies WHERE id=?", (movie_id,)).fetchone():
            db.execute(
                "INSERT INTO movies(id,title,is_listed) VALUES(?,?,0)",
                (movie_id, "Unknown movie"),
            )
        screening_id = _get_or_create_screening(
            db, movie_id, old["theatre"], old["show_date"], old["show_time"]
        )
        db.execute(
            """INSERT INTO bookings(id,screening_id,total,payment_status,status,created_at,user_id)
               VALUES(?,?,?,?,?,?,?)""",
            (
                old["id"],
                screening_id,
                old["total"],
                old["payment_status"],
                old["status"],
                old["created_at"],
                old["user_id"],
            ),
        )
        is_reserved = 1 if old["status"] == "confirmed" else 0
        for seat in dict.fromkeys(json.loads(old["seats"])):
            db.execute(
                "INSERT OR IGNORE INTO booking_seats(screening_id,booking_id,seat,is_reserved) VALUES(?,?,?,?)",
                (screening_id, old["id"], seat, is_reserved),
            )
    db.execute("DROP TABLE bookings_legacy")


def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return (
                jsonify(
                    {"error": "Please sign in to continue.", "login_required": True}
                ),
                401,
            )
        return fn(*args, **kwargs)

    return wrapped


@app.get("/api/auth/status")
def auth_status():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify(
            {
                "user": None,
                "oauth_configured": bool(
                    os.environ.get("GOOGLE_CLIENT_ID")
                    and os.environ.get("GOOGLE_CLIENT_SECRET")
                ),
            }
        )
    with connect() as db:
        user = db.execute(
            "SELECT id,email,name,picture FROM users WHERE id=?", (user_id,)
        ).fetchone()
    if not user:
        session.clear()
        return jsonify(
            {
                "user": None,
                "oauth_configured": bool(
                    os.environ.get("GOOGLE_CLIENT_ID")
                    and os.environ.get("GOOGLE_CLIENT_SECRET")
                ),
            }
        )
    return jsonify({"user": dict(user), "oauth_configured": True})


@app.get("/auth/google")
def auth_google():
    if not (
        os.environ.get("GOOGLE_CLIENT_ID") and os.environ.get("GOOGLE_CLIENT_SECRET")
    ):
        return redirect("/?auth_error=oauth_not_configured")
    callback_url = os.environ.get("OAUTH_REDIRECT_URI") or url_for(
        "google_callback", _external=True
    )
    return google.authorize_redirect(callback_url)


@app.get("/auth/callback")
def google_callback():
    if not google:
        return redirect("/?auth_error=oauth_not_configured")
    try:
        token = google.authorize_access_token()
        info = token["userinfo"]
        google_sub = info.get("sub")
        email = info.get("email")
        if not google_sub or not email or not info.get("email_verified", False):
            return redirect("/?auth_error=google_email_unverified")
        user_id = "usr_" + google_sub
        with connect() as db:
            db.execute(
                "INSERT INTO users(id,google_sub,email,name,picture,created_at) VALUES(?,?,?,?,?,?) ON CONFLICT(google_sub) DO UPDATE SET email=excluded.email,name=excluded.name,picture=excluded.picture",
                (
                    user_id,
                    google_sub,
                    email,
                    info.get("name") or email.split("@")[0],
                    info.get("picture"),
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            user = db.execute(
                "SELECT id,email,name,picture FROM users WHERE google_sub=?",
                (google_sub,),
            ).fetchone()
        session.clear()
        session["user_id"] = user["id"]
        return redirect("/")
    except Exception:
        app.logger.exception("Google OAuth sign-in failed")
        return redirect("/?auth_error=oauth_failed")


@app.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


def booking_dict(row):
    item = dict(row)
    with connect() as db:
        item["seats"] = [
            seat["seat"]
            for seat in db.execute(
                "SELECT seat FROM booking_seats WHERE booking_id=? ORDER BY seat",
                (item["id"],),
            ).fetchall()
        ]
    return item


@app.get("/api/movies")
def movies():
    with connect() as db:
        catalog = [
            dict(row)
            for row in db.execute(
                "SELECT id,title,release_date,year,poster,accent,genre,language,rating,duration,tag,description "
                "FROM movies WHERE is_listed=1 AND release_date IS NOT NULL"
            ).fetchall()
        ]
    return jsonify(movie_catalog(catalog, datetime.now().date()))


@app.get("/api/options")
def options():
    city = request.args.get("city")
    with connect() as db:
        if city:
            rows = db.execute(
                """SELECT t.name FROM theatres t JOIN cities c ON c.id=t.city_id
                   WHERE t.active=1 AND c.name=? ORDER BY t.name""",
                (city,),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT name FROM theatres WHERE active=1 ORDER BY name"
            ).fetchall()
    return jsonify(
        booking_options(datetime.now().date(), [row["name"] for row in rows], SHOWTIMES)
    )


@app.get("/api/cities")
def cities():
    with connect() as db:
        rows = db.execute(
            "SELECT name,latitude AS lat,longitude AS lon FROM cities ORDER BY name"
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.get("/api/seats")
def seats():
    movie, theatre = request.args.get("movie"), request.args.get("theatre")
    date, time = request.args.get("date"), request.args.get("time")
    if not all([movie, theatre, date, time]):
        return jsonify({"error": "Choose a movie, theatre, date and showtime."}), 400
    with connect() as db:
        rows = db.execute(
            """SELECT bs.seat FROM booking_seats bs
               JOIN screenings sc ON sc.id=bs.screening_id
               JOIN screens s ON s.id=sc.screen_id
               JOIN theatres t ON t.id=s.theatre_id
               JOIN bookings b ON b.id=bs.booking_id
               WHERE sc.movie_id=? AND t.name=? AND sc.show_date=? AND sc.show_time=?
                 AND b.status='confirmed' AND bs.is_reserved=1""",
            (movie, theatre, date, time),
        ).fetchall()
    return jsonify({"booked": [r["seat"] for r in rows]})


@app.get("/api/bookings")
@login_required
def bookings():
    with connect() as db:
        rows = db.execute(
            """SELECT b.id,sc.movie_id,m.title AS movie,t.name AS theatre,sc.show_date,sc.show_time,
                      b.total,b.payment_status,b.status,b.created_at,b.user_id
               FROM bookings b
               JOIN screenings sc ON sc.id=b.screening_id
               JOIN screens s ON s.id=sc.screen_id
               JOIN theatres t ON t.id=s.theatre_id
               JOIN movies m ON m.id=sc.movie_id
               WHERE b.status='confirmed' AND b.user_id=? ORDER BY b.created_at DESC""",
            (session["user_id"],),
        ).fetchall()
    return jsonify([booking_dict(r) for r in rows])


@app.post("/api/bookings")
@login_required
def create_booking():
    data = request.get_json(silent=True) or {}
    with connect() as db:
        catalog = [
            dict(row)
            for row in db.execute(
                "SELECT id,title,release_date,year,poster,accent FROM movies WHERE is_listed=1 AND release_date IS NOT NULL"
            ).fetchall()
        ]
        theatres = [
            row["name"]
            for row in db.execute("SELECT name FROM theatres WHERE active=1").fetchall()
        ]
    try:
        booking = validate_booking(
            data, catalog, theatres, SHOWTIMES, datetime.now().date()
        )
    except BookingValidationError as error:
        return jsonify({"error": str(error)}), error.status_code
    movie, theatre, date, time, chosen = (
        booking.movie_id,
        booking.theatre,
        booking.show_date,
        booking.show_time,
        booking.seats,
    )
    booking_id = "SM-" + uuid.uuid4().hex[:8].upper()
    now = datetime.now().isoformat(timespec="seconds")
    try:
        with connect() as db:
            screening_id = _get_or_create_screening(db, movie, theatre, date, time)
            db.execute(
                "INSERT INTO bookings(id,screening_id,total,payment_status,status,created_at,user_id) VALUES(?,?,?,?,?,?,?)",
                (
                    booking_id,
                    screening_id,
                    len(chosen) * 14,
                    "simulated_success",
                    "confirmed",
                    now,
                    session["user_id"],
                ),
            )
            db.executemany(
                "INSERT INTO booking_seats(screening_id,booking_id,seat,is_reserved) VALUES(?,?,?,1)",
                [(screening_id, booking_id, seat) for seat in chosen],
            )
    except sqlite3.IntegrityError:
        return (
            jsonify(
                {
                    "error": "One or more seats were just booked. Please choose different seats."
                }
            ),
            409,
        )
    with connect() as db:
        row = db.execute(
            """SELECT b.id,sc.movie_id,m.title AS movie,t.name AS theatre,sc.show_date,sc.show_time,
                      b.total,b.payment_status,b.status,b.created_at,b.user_id
               FROM bookings b JOIN screenings sc ON sc.id=b.screening_id
               JOIN screens s ON s.id=sc.screen_id
               JOIN theatres t ON t.id=s.theatre_id
               JOIN movies m ON m.id=sc.movie_id WHERE b.id=?""",
            (booking_id,),
        ).fetchone()
    return jsonify(booking_dict(row)), 201


@app.delete("/api/bookings/<booking_id>")
@login_required
def cancel_booking(booking_id):
    with connect() as db:
        cur = db.execute(
            "UPDATE bookings SET status='cancelled' WHERE id=? AND user_id=? AND status='confirmed'",
            (booking_id, session["user_id"]),
        )
        if cur.rowcount:
            db.execute(
                "UPDATE booking_seats SET is_reserved=0 WHERE booking_id=?",
                (booking_id,),
            )
            return jsonify({"message": "Booking cancelled. Seats are available again."})
    return jsonify({"error": "That booking could not be found."}), 404


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/<path:path>")
def static_files(path):
    return send_from_directory(app.static_folder, path)


if __name__ == "__main__":
    init_db()
    app.run(
        host=os.environ.get("HOST", "::1"),
        debug=os.environ.get("FLASK_DEBUG") == "1",
        port=int(os.environ.get("PORT", 5000)),
    )
