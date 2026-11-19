"""Unit tests for the booking and movie catalog service layer."""

import unittest
from datetime import date, datetime, timezone

from services import (
    BookingValidationError,
    booking_options,
    movie_catalog,
    validate_booking,
)

MOVIES = [
    {"id": "premiere", "title": "Premiere", "release_date": "2026-11-13"},
    {"id": "already-out", "title": "Already Out", "release_date": "2026-11-01"},
]
THEATRES = ["The Grand Cinema"]
SHOWTIMES = ["6:45 PM"]
TODAY = date(2026, 11, 6)


def valid_payload(**overrides):
    payload = {
        "movie_id": "premiere",
        "theatre": "The Grand Cinema",
        "show_date": "2026-11-13",
        "show_time": "6:45 PM",
        "seats": ["A1", "A2"],
        "payment_method": "simulated-card",
    }
    payload.update(overrides)
    return payload


class MovieCatalogTests(unittest.TestCase):

    # validates correct labelling based on the release date
    def test_catalog_adds_release_and_booking_status_and_sorts(self):
        catalog = movie_catalog(MOVIES, TODAY)

        self.assertEqual(
            [movie["id"] for movie in catalog], ["already-out", "premiere"]
        )
        self.assertEqual(catalog[0]["status"], "now_showing")
        self.assertTrue(catalog[0]["booking_open"])
        self.assertEqual(catalog[1]["status"], "coming_soon")
        self.assertTrue(catalog[1]["booking_open"])
        self.assertEqual(catalog[1]["booking_opens"], "2026-11-06")

    # validates if the movie if open for booking 7 days before release
    def test_upcoming_movie_booking_opens_seven_days_before_release(self):
        catalog = movie_catalog(MOVIES, date(2026, 11, 5))

        premiere = next(movie for movie in catalog if movie["id"] == "premiere")
        self.assertFalse(premiere["booking_open"])

    # validate if booking options include 14 dates, starting today, and the expected sample ticket price
    def test_booking_options_contains_fourteen_local_dates(self):
        options = booking_options(TODAY, THEATRES, SHOWTIMES)

        self.assertEqual(len(options["dates"]), 14)
        self.assertEqual(options["dates"][0], "2026-11-06")
        self.assertEqual(options["dates"][-1], "2026-11-19")
        self.assertEqual(options["seat_price"], 14)

    def test_booking_options_includes_cinema_timezone(self):
        options = booking_options(
            TODAY, THEATRES, SHOWTIMES, timezone_name="America/New_York"
        )

        self.assertEqual(options["timezone"], "America/New_York")


class BookingValidationTests(unittest.TestCase):

    def assert_invalid(self, payload, message, status=400):
        with self.assertRaises(BookingValidationError) as context:
            validate_booking(payload, MOVIES, THEATRES, SHOWTIMES, TODAY)
        self.assertEqual(str(context.exception), message)
        self.assertEqual(context.exception.status_code, status)

    # validate if a clean payload gives successful booking
    def test_valid_booking_returns_normalized_booking(self):
        booking = validate_booking(valid_payload(), MOVIES, THEATRES, SHOWTIMES, TODAY)

        self.assertEqual(booking.movie_id, "premiere")
        self.assertEqual(booking.show_date, "2026-11-13")
        self.assertEqual(booking.seats, ("A1", "A2"))
        self.assertEqual(booking.payment_method, "simulated-card")

    # validate that a request that isn’t an object is rejected
    def test_rejects_non_object_payload(self):
        self.assert_invalid(
            [], "Please choose a movie, showtime and at least one seat."
        )

    # validate that an invalid movie id is rejected
    def test_rejects_unhashable_movie_identifier(self):
        self.assert_invalid(
            {**valid_payload(), "movie_id": []},
            "Please choose a movie, showtime and at least one seat.",
        )

    # validate rejection when booking is done before booking window
    def test_rejects_booking_before_booking_window(self):
        with self.assertRaises(BookingValidationError) as context:
            validate_booking(
                valid_payload(), MOVIES, THEATRES, SHOWTIMES, date(2026, 11, 5)
            )
        self.assertEqual(context.exception.status_code, 409)
        self.assertIn("Booking opens on Nov 06", str(context.exception))

    # validate that past showtime is  invalid
    def test_rejects_a_showtime_that_has_already_passed_today(self):
        payload = valid_payload(
            movie_id="already-out", show_date="2026-11-06", show_time="6:45 PM"
        )
        now = datetime(2026, 11, 7, 1, 0, tzinfo=timezone.utc)

        with self.assertRaises(BookingValidationError) as context:
            validate_booking(
                payload,
                MOVIES,
                THEATRES,
                ["6:45 PM"],
                date(2026, 11, 6),
                now=now,
                timezone_name="America/Chicago",
            )

        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(
            str(context.exception),
            "That showtime has already passed. Choose a future showtime.",
        )
    
    # validate future showtime booking is allowed
    def test_allows_a_later_showtime_today_in_cinema_local_time(self):
        payload = valid_payload(
            movie_id="already-out", show_date="2026-11-06", show_time="9:20 PM"
        )
        now = datetime(2026, 11, 7, 1, 0, tzinfo=timezone.utc)

        booking = validate_booking(
            payload,
            MOVIES,
            THEATRES,
            ["9:20 PM"],
            date(2026, 11, 6),
            now=now,
            timezone_name="America/Chicago",
        )

        self.assertEqual(booking.show_date, "2026-11-06")

    # validate that showtimes in past ca
    def test_showtime_past_check_uses_cinema_timezone(self):
        payload = valid_payload(
            movie_id="already-out", show_date="2026-11-06", show_time="6:45 PM"
        )
        now = datetime(2026, 11, 7, 1, 0, tzinfo=timezone.utc)

        booking = validate_booking(
            payload,
            MOVIES,
            THEATRES,
            ["6:45 PM"],
            date(2026, 11, 6),
            now=now,
            timezone_name="America/Los_Angeles",
        )

        self.assertEqual(booking.show_time, "6:45 PM")

    # validate rejection when booking is done before release date
    def test_rejects_screening_before_release_date(self):
        self.assert_invalid(
            valid_payload(show_date="2026-11-12"),
            "Choose a screening on or after the movie's release date.",
        )

    # validate when screening date is invalid
    def test_rejects_malformed_screening_date(self):
        self.assert_invalid(
            valid_payload(show_date="not-a-date"),
            "Choose a screening on or after the movie's release date.",
        )

    # validate rejection when movie payload is invalid
    def test_rejects_movie_with_malformed_release_date(self):
        movie_without_release_date = [{**MOVIES[0], "release_date": None}]
        with self.assertRaises(BookingValidationError) as context:
            validate_booking(
                valid_payload(), movie_without_release_date, THEATRES, SHOWTIMES, TODAY
            )
        self.assertEqual(
            str(context.exception), "This movie has an invalid release date."
        )

    # validate rejection when invalid seats are selected
    def test_rejects_invalid_and_duplicate_seats(self):
        self.assert_invalid(
            valid_payload(seats=["Z99"]), "One or more selected seats are invalid."
        )
        self.assert_invalid(
            valid_payload(seats=["A1", "A1"]), "One or more selected seats are invalid."
        )
        self.assert_invalid(
            valid_payload(seats=[{}]), "One or more selected seats are invalid."
        )

    # validate rejection when the payment method is invalid
    def test_rejects_unsupported_payment_method(self):
        self.assert_invalid(
            valid_payload(payment_method="real-card"),
            "Choose a simulated payment method.",
        )

    # validate invalid case when theatre is not available
    def test_requires_a_cinema_available_in_the_selected_location(self):
        self.assert_invalid(
            valid_payload(theatre=""),
            "Choose a cinema for your selected location.",
        )

    # validate payment decline option
    def test_reports_simulated_payment_decline(self):
        self.assert_invalid(
            valid_payload(simulate_failure=True),
            "Simulated payment declined. No charge was made; your seats are still available.",
            402,
        )


if __name__ == "__main__":
    unittest.main()
