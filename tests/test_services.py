"""Unit tests for the booking and movie catalog service layer."""

import unittest
from datetime import date

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

    def test_upcoming_movie_booking_opens_seven_days_before_release(self):
        catalog = movie_catalog(MOVIES, date(2026, 11, 5))

        premiere = next(movie for movie in catalog if movie["id"] == "premiere")
        self.assertFalse(premiere["booking_open"])

    def test_booking_options_contains_fourteen_local_dates(self):
        options = booking_options(TODAY, THEATRES, SHOWTIMES)

        self.assertEqual(len(options["dates"]), 14)
        self.assertEqual(options["dates"][0], "2026-11-06")
        self.assertEqual(options["dates"][-1], "2026-11-19")
        self.assertEqual(options["seat_price"], 14)


class BookingValidationTests(unittest.TestCase):
    def assert_invalid(self, payload, message, status=400):
        with self.assertRaises(BookingValidationError) as context:
            validate_booking(payload, MOVIES, THEATRES, SHOWTIMES, TODAY)
        self.assertEqual(str(context.exception), message)
        self.assertEqual(context.exception.status_code, status)

    def test_valid_booking_returns_normalized_booking(self):
        booking = validate_booking(valid_payload(), MOVIES, THEATRES, SHOWTIMES, TODAY)

        self.assertEqual(booking.movie_id, "premiere")
        self.assertEqual(booking.show_date, "2026-11-13")
        self.assertEqual(booking.seats, ("A1", "A2"))
        self.assertEqual(booking.payment_method, "simulated-card")

    def test_rejects_non_object_payload(self):
        self.assert_invalid(
            [], "Please choose a movie, showtime and at least one seat."
        )

    def test_rejects_unhashable_movie_identifier(self):
        self.assert_invalid(
            {**valid_payload(), "movie_id": []},
            "Please choose a movie, showtime and at least one seat.",
        )

    def test_rejects_booking_before_booking_window(self):
        with self.assertRaises(BookingValidationError) as context:
            validate_booking(
                valid_payload(), MOVIES, THEATRES, SHOWTIMES, date(2026, 11, 5)
            )
        self.assertEqual(context.exception.status_code, 409)
        self.assertIn("Booking opens on Nov 06", str(context.exception))

    def test_rejects_screening_before_release_date(self):
        self.assert_invalid(
            valid_payload(show_date="2026-11-12"),
            "Choose a screening on or after the movie's release date.",
        )

    def test_rejects_malformed_screening_date(self):
        self.assert_invalid(
            valid_payload(show_date="not-a-date"),
            "Choose a screening on or after the movie's release date.",
        )

    def test_rejects_movie_with_malformed_release_date(self):
        movie_without_release_date = [{**MOVIES[0], "release_date": None}]
        with self.assertRaises(BookingValidationError) as context:
            validate_booking(
                valid_payload(), movie_without_release_date, THEATRES, SHOWTIMES, TODAY
            )
        self.assertEqual(
            str(context.exception), "This movie has an invalid release date."
        )

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

    def test_rejects_unsupported_payment_method(self):
        self.assert_invalid(
            valid_payload(payment_method="real-card"),
            "Choose a simulated payment method.",
        )

    def test_reports_simulated_payment_decline(self):
        self.assert_invalid(
            valid_payload(simulate_failure=True),
            "Simulated payment declined. No charge was made; your seats are still available.",
            402,
        )


if __name__ == "__main__":
    unittest.main()
