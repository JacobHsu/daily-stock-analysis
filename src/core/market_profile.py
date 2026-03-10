# -*- coding: utf-8 -*-
"""
大盘复盘市场区域配置 (US-only)
"""

from dataclasses import dataclass
from typing import List


@dataclass
class MarketProfile:
    """大盘复盘市场区域配置"""

    region: str
    mood_index_code: str
    news_queries: List[str]
    prompt_index_hint: str
    has_market_stats: bool
    has_sector_rankings: bool


US_PROFILE = MarketProfile(
    region="us",
    mood_index_code="SPX",
    news_queries=[
        "美股 大盘",
        "US stock market",
        "S&P 500 NASDAQ",
    ],
    prompt_index_hint="分析标普500、纳斯达克、道指等各指数走势特点",
    has_market_stats=False,
    has_sector_rankings=False,
)


def get_profile(region: str) -> MarketProfile:
    """返回 US_PROFILE（唯一支持市场）"""
    return US_PROFILE
