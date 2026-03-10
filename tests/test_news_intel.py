# -*- coding: utf-8 -*-
"""
Unit tests for news intel storage deduplication logic.
"""

import os
import tempfile
import unittest

from datetime import datetime

from src.config import Config
from src.storage import DatabaseManager, NewsIntel
from src.search_service import SearchResponse, SearchResult


class NewsIntelStorageTestCase(unittest.TestCase):
    """新闻情报存储测试"""

    def setUp(self) -> None:
        """为每个用例初始化独立数据库"""
        self._temp_dir = tempfile.TemporaryDirectory()
        self._db_path = os.path.join(self._temp_dir.name, "test_news_intel.db")
        os.environ["DATABASE_PATH"] = self._db_path

        # 重置配置与数据库单例，确保使用临时库
        Config._instance = None
        DatabaseManager.reset_instance()
        self.db = DatabaseManager.get_instance()

    def tearDown(self) -> None:
        """清理资源"""
        DatabaseManager.reset_instance()
        self._temp_dir.cleanup()

    def _build_response(self, results) -> SearchResponse:
        """Build a SearchResponse for testing."""
        return SearchResponse(
            query="Apple Inc. latest news",
            results=results,
            provider="Bocha",
            success=True,
        )

    def test_save_news_intel_with_url_dedup(self) -> None:
        """Same URL should be deduplicated, only one record saved."""
        result = SearchResult(
            title="Apple launches new product",
            snippet="The company unveiled...",
            url="https://news.example.com/a",
            source="example.com",
            published_date="2025-01-02"
        )
        response = self._build_response([result])

        query_context = {
            "query_id": "task_001",
            "query_source": "bot",
            "requester_platform": "feishu",
            "requester_user_id": "u_123",
            "requester_user_name": "test_user",
            "requester_chat_id": "c_456",
            "requester_message_id": "m_789",
            "requester_query": "/analyze AAPL",
        }

        saved_first = self.db.save_news_intel(
            code="AAPL",
            name="Apple Inc.",
            dimension="latest_news",
            query=response.query,
            response=response,
            query_context=query_context
        )
        saved_second = self.db.save_news_intel(
            code="AAPL",
            name="Apple Inc.",
            dimension="latest_news",
            query=response.query,
            response=response,
            query_context=query_context
        )

        self.assertEqual(saved_first, 1)
        self.assertEqual(saved_second, 0)

        with self.db.get_session() as session:
            total = session.query(NewsIntel).count()
            row = session.query(NewsIntel).first()
        self.assertEqual(total, 1)
        if row is None:
            self.fail("未找到保存的新闻记录")
        self.assertEqual(row.query_id, "task_001")
        self.assertEqual(row.requester_user_name, "test_user")

    def test_save_news_intel_without_url_fallback_key(self) -> None:
        """Fallback dedup key used when URL is empty."""
        result = SearchResult(
            title="Apple earnings preview",
            snippet="Strong growth expected...",
            url="",
            source="example.com",
            published_date="2025-01-03"
        )
        response = self._build_response([result])

        saved_first = self.db.save_news_intel(
            code="AAPL",
            name="Apple Inc.",
            dimension="earnings",
            query=response.query,
            response=response
        )
        saved_second = self.db.save_news_intel(
            code="AAPL",
            name="Apple Inc.",
            dimension="earnings",
            query=response.query,
            response=response
        )

        self.assertEqual(saved_first, 1)
        self.assertEqual(saved_second, 0)

        with self.db.get_session() as session:
            row = session.query(NewsIntel).first()
            if row is None:
                self.fail("未找到保存的新闻记录")
            self.assertTrue(row.url.startswith("no-url:"))

    def test_get_recent_news(self) -> None:
        """Can query recent news by time range."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = SearchResult(
            title="Apple stock volatility",
            snippet="Intraday swings...",
            url="https://news.example.com/b",
            source="example.com",
            published_date=now
        )
        response = self._build_response([result])

        self.db.save_news_intel(
            code="AAPL",
            name="Apple Inc.",
            dimension="market_analysis",
            query=response.query,
            response=response
        )

        recent_news = self.db.get_recent_news(code="AAPL", days=7, limit=10)
        self.assertEqual(len(recent_news), 1)
        self.assertEqual(recent_news[0].title, "Apple stock volatility")


if __name__ == "__main__":
    unittest.main()
