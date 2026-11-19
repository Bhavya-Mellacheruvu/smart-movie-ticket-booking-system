"""Business rules for movie discovery and ticket booking."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo


class BookingValidationError(ValueError):
    """A booking request that cannot be accepted by the application."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class ValidatedBooking:
    movie_id: str
    theatre: str
    show_date: str
    show_time: str
    seats: tuple[str, ...]
    payment_method: str
    movie: Mapping[str, Any]


def movie_catalog(
    movies: Iterable[Mapping[str, Any]], today: date
) -> list[dict[str, Any]]:
    """Return sorted movie data with booking and release status fields."""
    ordered = sorted(
        movies, key=lambda movie: (movie["release_date"], movie["title"].casefold())
    )
    result = []
    for movie in ordered:
        release_date = date.fromisoformat(movie["release_date"])
        booking_opens = release_date - timedelta(days=7)
        status = "coming_soon" if release_date > today else "now_showing"
        result.append(
            {
                **movie,
                "status": status,
                "tag": "COMING SOON" if status == "coming_soon" else "NOW SHOWING",
                "booking_opens": booking_opens.isoformat(),
                "booking_open": today >= booking_opens,
            }
        )
    return result


def booking_options(
    today: date,
    theatres: Iterable[str],
    times: Iterable[str],
    days: int = 14,
    seat_price: int = 14,
    timezone_name: str = "America/Chicago",
) -> dict[str, Any]:
    """Build the date and venue options shown by the booking UI."""
    dates = [(today + timedelta(days=offset)).isoformat() for offset in range(days)]
    return {
        "theatres": list(theatres),
        "times": list(times),
        "dates": dates,
        "seat_price": seat_price,
        "timezone": timezone_name,
    }


def screening_is_past(
    show_date: str,
    show_time: str,
    now: datetime | None = None,
    timezone_name: str = "America/Chicago",
) -> bool:
    """Return whether a screening has started in the cinema's local timezone."""
    zone = ZoneInfo(timezone_name)
    screening = datetime.combine(
        date.fromisoformat(show_date), datetime.strptime(show_time, "%I:%M %p").time()
    ).replace(tzinfo=zone)
    current = now or datetime.combine(
        date.fromisoformat(show_date), datetime.min.time(), tzinfo=zone
    )
    if current.tzinfo is None:
        current = current.replace(tzinfo=zone)
    else:
        current = current.astimezone(zone)
    return screening <= current


def validate_booking(
    data: Any,
    movies: Iterable[Mapping[str, Any]],
    theatres: Iterable[str],
    showtimes: Iterable[str],
    today: date,
    now: datetime | None = None,
    timezone_name: str = "America/Chicago",
) -> ValidatedBooking:
    """Validate booking input and return normalized values for persistence."""
    if not isinstance(data, dict):
        data = {}

    movie_id = data.get("movie_id")
    theatre = data.get("theatre")
    show_date = data.get("show_date")
    show_time = data.get("show_time")
    seats = data.get("seats")
    movie_by_id = {movie["id"]: movie for movie in movies}

    if (
        not isinstance(movie_id, str)
        or movie_id not in movie_by_id
        or not isinstance(show_time, str)
        or show_time not in showtimes
        or not isinstance(seats, list)
        or not seats
    ):
        raise BookingValidationError(
            "Please choose a movie, showtime and at least one seat."
        )
    if not isinstance(theatre, str) or theatre not in theatres:
        raise BookingValidationError("Choose a cinema for your selected location.")

    movie = movie_by_id[movie_id]
    try:
        release_date = date.fromisoformat(movie["release_date"])
    except (TypeError, ValueError) as error:
        raise BookingValidationError(
            "This movie has an invalid release date."
        ) from error
    booking_opens = release_date - timedelta(days=7)
    if today < booking_opens:
        raise BookingValidationError(
            f"Booking opens on {booking_opens.strftime('%b %d')} (7 days before release).",
            409,
        )

    try:
        screening_date = (
            date.fromisoformat(show_date) if isinstance(show_date, str) else None
        )
    except ValueError:
        screening_date = None
    if screening_date is None or screening_date < release_date:
        raise BookingValidationError(
            "Choose a screening on or after the movie's release date."
        )
    if screening_is_past(screening_date.isoformat(), show_time, now, timezone_name):
        raise BookingValidationError(
            "That showtime has already passed. Choose a future showtime.", 409
        )

    allowed_seats = {f"{row}{column}" for row in "ABCDEFGH" for column in range(1, 11)}
    if any(
        not isinstance(seat, str) or seat not in allowed_seats for seat in seats
    ) or len(seats) != len(set(seats)):
        raise BookingValidationError("One or more selected seats are invalid.")

    payment_method = data.get("payment_method")
    if payment_method not in ("simulated-card", "at-counter"):
        raise BookingValidationError("Choose a simulated payment method.")
    if data.get("simulate_failure"):
        raise BookingValidationError(
            "Simulated payment declined. No charge was made; your seats are still available.",
            402,
        )

    return ValidatedBooking(
        movie_id=movie_id,
        theatre=theatre,
        show_date=screening_date.isoformat(),
        show_time=show_time,
        seats=tuple(seats),
        payment_method=payment_method,
        movie=movie,
    )
