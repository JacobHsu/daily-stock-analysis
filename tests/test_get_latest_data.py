# -*- coding: utf-8 -*-
"""
Tests for DatabaseManager.get_latest_data method.
"""

import os
import tempfile
import unittest
from datetime import date, timedelta

import pandas as pd

from src.config import Config
from src.storage import DatabaseManager, StockDaily


class GetLatestDataTestCase(unittest.TestCase):
    """Tests for DatabaseManager.get_latest_data."""

    def setUp(self) -> None:
        """Initialize an isolated database for each test case."""
        self._temp_dir = tempfile.TemporaryDirectory()
        self._db_path = os.path.join(self._temp_dir.name, "test_get_latest_data.db")
        os.environ["DATABASE_PATH"] = self._db_path

        Config._instance = None
        DatabaseManager.reset_instance()
        self.db = DatabaseManager.get_instance()

    def tearDown(self) -> None:
        """Clean up resources."""
        DatabaseManager.reset_instance()
        self._temp_dir.cleanup()

    def _insert_stock_data(self, code: str, days_ago: int, close: float) -> None:
        """Insert test stock data."""
        target_date = date.today() - timedelta(days=days_ago)
        df = pd.DataFrame([{
            'date': target_date,
            'open': close - 1,
            'high': close + 1,
            'low': close - 2,
            'close': close,
            'volume': 1000000,
            'amount': 10000000,
            'pct_chg': 1.5,
        }])
        self.db.save_daily_data(df, code, data_source="TestData")

    def test_get_latest_data_returns_empty_when_no_data(self) -> None:
        """Returns empty list when no data exists."""
        result = self.db.get_latest_data("MSFT", days=2)
        self.assertEqual(result, [])

    def test_get_latest_data_returns_correct_count(self) -> None:
        """Returns the correct number of rows."""
        for i in range(5):
            self._insert_stock_data("AAPL", days_ago=i, close=100.0 + i)

        result = self.db.get_latest_data("AAPL", days=2)
        self.assertEqual(len(result), 2)

        result = self.db.get_latest_data("AAPL", days=5)
        self.assertEqual(len(result), 5)

    def test_get_latest_data_ordered_by_date_desc(self) -> None:
        """Verifies data is returned in descending date order."""
        for i in range(3):
            self._insert_stock_data("AAPL", days_ago=i, close=100.0 + i)

        result = self.db.get_latest_data("AAPL", days=3)

        self.assertEqual(len(result), 3)
        self.assertGreater(result[0].date, result[1].date)
        self.assertGreater(result[1].date, result[2].date)

    def test_get_latest_data_filters_by_code(self) -> None:
        """Verifies filtering by stock code."""
        self._insert_stock_data("AAPL", days_ago=0, close=100.0)
        self._insert_stock_data("TSLA", days_ago=0, close=50.0)

        result = self.db.get_latest_data("AAPL", days=5)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].code, "AAPL")


if __name__ == "__main__":
    unittest.main()
