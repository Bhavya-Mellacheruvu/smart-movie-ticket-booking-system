"""HTTP boundary tests for the Flask API."""

import unittest
from unittest.mock import Mock, patch

from app import app, connect


class CityEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

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
    @patch("app.sqlite3.connect")
    def test_connection_commits_and_closes_after_success(self, sqlite_connect):
        database = Mock()
        sqlite_connect.return_value = database

        with connect() as opened_database:
            self.assertIs(opened_database, database)

        database.commit.assert_called_once_with()
        database.rollback.assert_not_called()
        database.close.assert_called_once_with()

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
