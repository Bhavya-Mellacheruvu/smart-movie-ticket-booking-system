# iMovieTickets — Smart Movie Ticket Booking System
[![Python Unit Tests](https://github.com/Bhavya-Mellacheruvu/smart-movie-ticket-booking-system/actions/workflows/test.yml/badge.svg)](https://github.com/Bhavya-Mellacheruvu/smart-movie-ticket-booking-system/actions/workflows/test.yml)
## Project summary

The Smart Movie Ticket Booking System is a local web prototype for browsing recent and upcoming U.S. movie releases, viewing sample cinemas and showtimes, selecting seats, and managing bookings. The Discover page features a rotating movie banner and a searchable catalog, with separate views for movies now showing and coming soon. The frontend uses React with Vite, while a Python Flask API handles movie, seat, booking, and cancellation requests. Booking rules live in a separate service module, and records are stored in a local SQLite database (`movie_bookings.sqlite3`).

All movies, cinemas, showtimes, prices, bookings, and payment outcomes are sample data. Checkout simulates success or failure without collecting card details or making real payments. This prototype uses SQLite rather than MySQL so it can run locally without a database server; the relational booking data can be migrated to MySQL if required for deployment.

## Project structure

```text
app.py                       Flask routes, OAuth setup, and database startup
services.py                  Movie catalog and booking rules
tests/                       Service and API boundary tests
web/src/App.jsx               React app state and navigation
web/src/pages/                Discover, booking, sign-in, and bookings views
web/src/components/           Shared poster, header, footer, and location UI
web/src/api.js                Fetch client for the Flask API
web/*.css                     Responsive UI styles
*_seed.json                   Sample movie, city, and theatre data
package.json                  Frontend scripts and dependencies
vite.config.js                Development proxy and production build setup
```

The React app is split into page-level views (`DiscoverPage`, `BookingPage`, `BookingsPage`, and `SignInPage`) plus shared components such as `Poster`, `CityPicker`, `SiteHeader`, and `Footer`. The app shell owns navigation and shared state; API requests and booking rules live outside the view components.

## Database design

- `movies` stores the current catalog and the older movie records referenced by existing bookings. The `/api/movies` endpoint reads listed movies from SQLite; release status and booking-open dates are calculated when the API responds.
- `cities` stores supported locations and coordinates. The city picker reads these from `/api/cities`.
- `theatres` belong to a city, and `screens` belong to a theatre.
- `screenings` assigns a movie to a screen on a date and showtime. This is how movies are related to theatres.
- `bookings` stores the customer, screening, total, payment outcome, and booking status.
- `booking_seats` stores each reserved seat and links it to both its booking and screening. A unique screening/seat key prevents two confirmed bookings from taking the same seat.
- `users` stores Google account details used by sign-in.

On a new or empty database, the app inserts the initial movie catalog from `movie_catalog_seed.json`, city data from `city_seed.json`, and sample venues/screens from `theatre_seed.json`. The sample venues are split across Columbus (3) and Cleveland (2). Existing bookings and screenings are migrated at startup. Canceled booking seat assignments remain in `booking_seats` with `is_reserved=0`, preserving history while making those seats available again.

The five demo showtimes are still shared sample options. A screening row is created for the selected movie and the theatre's active screen when a booking succeeds; a separately managed future schedule is not part of this change.

## Run locally

1. Install Python 3.11+ and Node.js 20.19+.
2. From the project folder, create and activate a virtual environment: `python3 -m venv .venv && source .venv/bin/activate`.
3. Install backend and frontend dependencies: `python -m pip install -r requirements.txt` and `npm install`.
4. Build the React frontend: `npm run build`.
5. Start the app: `python app.py`.
6. Open [http://localhost:5000](http://localhost:5000).

For frontend development, run `python app.py` in one terminal and `npm run dev` in another, then open [http://localhost:5173](http://localhost:5173). Vite proxies API and authentication requests to Flask.

## Run unit tests

From the project folder, run `python -m unittest discover -s tests -v` to test movie catalog and booking rules, the cities API response using a mock database, and database connection cleanup without modifying booking data. Python formatting and lint settings are in `pyproject.toml`.

The project ignores local credentials, virtual environments, caches, and SQLite files. Keep `.env.example` as the safe configuration template; never commit `.env`.

## Google sign-in setup

The app supports account creation and sign-in through Google OAuth. Create an OAuth 2.0 Web application client in Google Cloud Console and add the callback URL you use as an authorized redirect URI: `http://127.0.0.1:5000/auth/callback` or `http://localhost:5000/auth/callback`. Store `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `FLASK_SECRET_KEY` in the local `.env` file. A starter template is provided as `.env.example`.

```dotenv
GOOGLE_CLIENT_ID="your-client-id"
GOOGLE_CLIENT_SECRET="your-client-secret"
FLASK_SECRET_KEY="a-long-random-secret"
```

Without Google OAuth credentials, the login and sign-up page is available but authentication cannot complete. Returning Google accounts are signed in, and new Google accounts are added to the local users table. Bookings are associated with the signed-in account.

Bookings are stored in `movie_bookings.sqlite3` next to the app. Set `MOVIE_DB` to use a different SQLite file or `PORT` to change the local port.

## Demo features

- Search and filter recent and upcoming U.S. releases through December 2026.
- Browse featured releases in the rotating Discover banner.
- Pre-book releases starting seven days before their scheduled U.S. release date.
- Select a sample cinema, date and screening.
- Choose seats in a live seating layout. Seat reservations are checked and stored atomically, preventing duplicate bookings for the same screening.
- Simulate successful checkout or tick “Simulate a declined payment” to demonstrate a declined transaction.
- View and cancel confirmed bookings; cancelled seats become available again.

All bookings and payment outcomes are simulated. The payment screen never asks for card information and does not process charges.

The React 18 frontend is bundled locally with Vite. Featured film posters use remote image URLs; CSS artwork is used as a fallback for other movies.
