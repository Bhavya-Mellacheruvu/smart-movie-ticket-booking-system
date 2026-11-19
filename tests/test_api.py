"""HTTP boundary tests for the Flask API."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from app import app, connect, init_db


class CityEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()


    # validate format of city rows returned
    @patch("app.connect")
    def test_cities_returns_rows_from_database(self, connect_mock):
        database = Mock()
        database.execute.return_value.fetchall.return_value = [
            {"name": "Chicago", "lat": 41.8781, "lon": -87.6298}
        ]
        connection = Mock()
        connection.__enter__ = Mock(return_value=database)
        connection.__exit__ = Mock(return_value=False)
        connect_mock.return_value = connection

        response = self.client.get("/api/cities")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            [{"name": "Chicago", "lat": 41.8781, "lon": -87.6298}],
        )
        database.execute.assert_called_once_with(
            "SELECT name,latitude AS lat,longitude AS lon FROM cities ORDER BY name"
        )


class DatabaseConnectionTests(unittest.TestCase):
    # validates that db connection commits and then closes successfully
    @patch("app.sqlite3.connect")
    def test_connection_commits_and_closes_after_success(self, sqlite_connect):
        database = Mock()
        sqlite_connect.return_value = database

        with connect() as opened_database:
            self.assertIs(opened_database, database)

        database.commit.assert_called_once_with()
        database.rollback.assert_not_called()
        database.close.assert_called_once_with()


class CancellationEndpointTests(unittest.TestCase):

    # validate booking in the past cannot be cancelled
    @patch("app.connect")
    def test_past_booking_cannot_be_cancelled(self, connect_mock):
        database = Mock()
        database.execute.return_value.fetchone.return_value = {
            "status": "confirmed",
            "show_date": "2000-01-01",
            "show_time": "10:30 AM",
            "timezone": "America/Chicago",
        }
        connection = Mock()
        connection.__enter__ = Mock(return_value=database)
        connection.__exit__ = Mock(return_value=False)
        connect_mock.return_value = connection

        client = app.test_client()
        with client.session_transaction() as session:
            session["user_id"] = "test-user"

        response = client.delete("/api/bookings/SM-PAST")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.get_json(),
            {"error": "Past showtimes can no longer be cancelled."},
        )
        database.execute.assert_called_once()


class CityVenueSeedTests(unittest.TestCase):

    def test_every_seeded_city_gets_a_cinema_and_seeding_is_idempotent(self):
        with (
            TemporaryDirectory() as temp_dir,
            patch("app.DB_PATH", Path(temp_dir) / "test.sqlite3"),
        ):
            init_db()

            with connect() as db:
                city_count = db.execute("SELECT COUNT(*) FROM cities").fetchone()[0]
                uncovered_cities = db.execute(
                    """SELECT c.name FROM cities c
                       LEFT JOIN theatres t ON t.city_id=c.id AND t.active=1
                       GROUP BY c.id HAVING COUNT(t.id)=0"""
                ).fetchall()
                theatre_count = db.execute(
                    "SELECT COUNT(*) FROM theatres WHERE active=1"
                ).fetchone()[0]

            self.assertGreater(city_count, 0)
            self.assertEqual(uncovered_cities, [])

            init_db()
            with connect() as db:
                self.assertEqual(
                    db.execute(
                        "SELECT COUNT(*) FROM theatres WHERE active=1"
                    ).fetchone()[0],
                    theatre_count,
                )

    # validate that when db commit fails, it roll backs and closes the connection
    @patch("app.sqlite3.connect")
    def test_connection_rolls_back_and_closes_after_error(self, sqlite_connect):
        database = Mock()
        sqlite_connect.return_value = database

        with self.assertRaisesRegex(RuntimeError, "database failure"):
            with connect():
                raise RuntimeError("database failure")

        database.commit.assert_not_called()
        database.rollback.assert_called_once_with()
        database.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
