# -*- coding: utf-8 -*-
"""
===================================
交易日历模块 (Issue #373)
===================================

职责：
1. 按市场（A股/港股/美股）判断当日是否为交易日
2. 按市场时区取“今日”日期，避免服务器 UTC 导致日期错误
3. 支持 per-stock 过滤：只分析当日开市市场的股票

依赖：exchange-calendars（可选，不可用时 fail-open）
"""

import logging
from datetime import date, datetime
from typing import Optional, Set

logger = logging.getLogger(__name__)

# Exchange-calendars availability
_XCALS_AVAILABLE = False
try:
    import exchange_calendars as xcals
    _XCALS_AVAILABLE = True
except ImportError:
    logger.warning(
        "exchange-calendars not installed; trading day check disabled. "
        "Run: pip install exchange-calendars"
    )

# Market -> exchange code (exchange-calendars)
MARKET_EXCHANGE = {"us": "XNYS"}

# Market -> IANA timezone for "today"
MARKET_TIMEZONE = {"us": "America/New_York"}


def get_market_for_stock(code: str) -> Optional[str]:
    """
    Infer market region for a stock code.
    Returns 'us' for recognized US stocks/indices, None otherwise (fail-open).
    """
    if not code or not isinstance(code, str):
        return None
    code = (code or "").strip().upper()
    from data_provider import is_us_stock_code, is_us_index_code
    if is_us_stock_code(code) or is_us_index_code(code):
        return "us"
    return None


def is_market_open(market: str, check_date: date) -> bool:
    """
    Check if the given market is open on the given date.

    Fail-open: returns True if exchange-calendars unavailable or date out of range.

    Args:
        market: 'cn' | 'hk' | 'us'
        check_date: Date to check

    Returns:
        True if trading day (or fail-open), False otherwise
    """
    if not _XCALS_AVAILABLE:
        return True
    ex = MARKET_EXCHANGE.get(market)
    if not ex:
        return True
    try:
        cal = xcals.get_calendar(ex)
        session = datetime(check_date.year, check_date.month, check_date.day)
        return cal.is_session(session)
    except Exception as e:
        logger.warning("trading_calendar.is_market_open fail-open: %s", e)
        return True


def get_open_markets_today() -> Set[str]:
    """
    Get markets open today (US only).
    Returns {'us'} if US market is open today, empty set otherwise.
    """
    if not _XCALS_AVAILABLE:
        return {"us"}
    result: Set[str] = set()
    from zoneinfo import ZoneInfo
    try:
        tz = ZoneInfo("America/New_York")
        today = datetime.now(tz).date()
        if is_market_open("us", today):
            result.add("us")
    except Exception as e:
        logger.warning("get_open_markets_today fail-open: %s", e)
        result.add("us")
    return result


def compute_effective_region(
    config_region: str, open_markets: Set[str]
) -> Optional[str]:
    """
    Compute effective market review region (US-only).
    Returns 'us' if US market is open, '' if closed, None if check disabled.
    """
    return "us" if "us" in open_markets else ""
