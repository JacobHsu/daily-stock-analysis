# -*- coding: utf-8 -*-
"""
===================================
資料來源基類與管理器
===================================

設計模式：策略模式 (Strategy Pattern)
- BaseFetcher: 抽象基類，定義統一介面
- DataFetcherManager: 策略管理器，實現自動切換

防封禁策略：
1. 每個 Fetcher 內建流控邏輯
2. 失敗自動切換到下一個資料來源
3. 指數退避重試機制
"""

import logging
import random
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any

import pandas as pd
import numpy as np
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.analyzer import STOCK_NAME_MAP

# 配置日誌
logger = logging.getLogger(__name__)


# === 標準化列名定義 ===
STANDARD_COLUMNS = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'pct_chg']


def normalize_stock_code(stock_code: str) -> str:
    """
    Normalize stock code to uppercase. For US stocks, returns the code as-is (uppercased).

    Examples:
        'aapl'  -> 'AAPL'
        'AAPL'  -> 'AAPL'
        'SPX'   -> 'SPX'
    """
    return (stock_code or "").strip().upper()


def canonical_stock_code(code: str) -> str:
    """
    Return the canonical (uppercase) form of a stock code.

    This is a display/storage layer concern, distinct from normalize_stock_code
    which strips exchange prefixes. Apply at system input boundaries to ensure
    consistent case across BOT, WEB UI, API, and CLI paths (Issue #355).

    Examples:
        'aapl'  -> 'AAPL'
        'AAPL'  -> 'AAPL'
    """
    return (code or "").strip().upper()


class DataFetchError(Exception):
    """資料獲取異常基類"""
    pass


class RateLimitError(DataFetchError):
    """API 速率限制異常"""
    pass


class DataSourceUnavailableError(DataFetchError):
    """資料來源不可用異常"""
    pass


class BaseFetcher(ABC):
    """
    資料來源抽象基類
    
    職責：
    1. 定義統一的資料獲取介面
    2. 提供資料標準化方法
    3. 實現通用的技術指標計算
    
    子類實現：
    - _fetch_raw_data(): 從具體資料來源獲取原始資料
    - _normalize_data(): 將原始資料轉換為標準格式
    """
    
    name: str = "BaseFetcher"
    priority: int = 99  # 優先順序數字越小越優先
    
    @abstractmethod
    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        從資料來源獲取原始資料（子類必須實現）
        
        Args:
            stock_code: 股票程式碼，如 'AAPL', 'TSLA'
            start_date: 開始日期，格式 'YYYY-MM-DD'
            end_date: 結束日期，格式 'YYYY-MM-DD'
            
        Returns:
            原始資料 DataFrame（列名因資料來源而異）
        """
        pass
    
    @abstractmethod
    def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """
        標準化資料列名（子類必須實現）

        將不同資料來源的列名統一為：
        ['date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'pct_chg']
        """
        pass

    def get_main_indices(self, region: str = "us") -> Optional[List[Dict[str, Any]]]:
        """
        獲取主要指數實時行情

        Args:
            region: 市場區域，目前僅支援 us=美股

        Returns:
            List[Dict]: 指數列表，每個元素為字典，包含:
                - code: 指數程式碼
                - name: 指數名稱
                - current: 當前點位
                - change: 漲跌點數
                - change_pct: 漲跌幅(%)
                - volume: 成交量
                - amount: 成交額
        """
        return None

    def get_market_stats(self) -> Optional[Dict[str, Any]]:
        """
        獲取市場漲跌統計

        Returns:
            Dict: 包含:
                - up_count: 上漲家數
                - down_count: 下跌家數
                - flat_count: 平盤家數
                - limit_up_count: 漲停家數
                - limit_down_count: 跌停家數
                - total_amount: 兩市成交額
        """
        return None

    def get_sector_rankings(self, n: int = 5) -> Optional[Tuple[List[Dict], List[Dict]]]:
        """
        獲取板塊漲跌榜

        Args:
            n: 返回前n個

        Returns:
            Tuple: (領漲板塊列表, 領跌板塊列表)
        """
        return None

    def get_daily_data(
        self,
        stock_code: str, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 30
    ) -> pd.DataFrame:
        """
        獲取日線資料（統一入口）
        
        流程：
        1. 計算日期範圍
        2. 呼叫子類獲取原始資料
        3. 標準化列名
        4. 計算技術指標
        
        Args:
            stock_code: 股票程式碼
            start_date: 開始日期（可選）
            end_date: 結束日期（可選，預設今天）
            days: 獲取天數（當 start_date 未指定時使用）
            
        Returns:
            標準化的 DataFrame，包含技術指標
        """
        # 計算日期範圍
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        if start_date is None:
            # 預設獲取最近 30 個交易日（按日曆日估算，多取一些）
            from datetime import timedelta
            start_dt = datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=days * 2)
            start_date = start_dt.strftime('%Y-%m-%d')
        
        logger.info(f"[{self.name}] 獲取 {stock_code} 資料: {start_date} ~ {end_date}")
        
        try:
            # Step 1: 獲取原始資料
            raw_df = self._fetch_raw_data(stock_code, start_date, end_date)
            
            if raw_df is None or raw_df.empty:
                raise DataFetchError(f"[{self.name}] 未獲取到 {stock_code} 的資料")
            
            # Step 2: 標準化列名
            df = self._normalize_data(raw_df, stock_code)
            
            # Step 3: 資料清洗
            df = self._clean_data(df)
            
            # Step 4: 計算技術指標
            df = self._calculate_indicators(df)
            
            logger.info(f"[{self.name}] {stock_code} 獲取成功，共 {len(df)} 條資料")
            return df
            
        except Exception as e:
            logger.error(f"[{self.name}] 獲取 {stock_code} 失敗: {str(e)}")
            raise DataFetchError(f"[{self.name}] {stock_code}: {str(e)}") from e
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        資料清洗
        
        處理：
        1. 確保日期列格式正確
        2. 數值型別轉換
        3. 去除空值行
        4. 按日期排序
        """
        df = df.copy()
        
        # 確保日期列為 datetime 型別
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        # 數值列型別轉換
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'amount', 'pct_chg']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 去除關鍵列為空的行
        df = df.dropna(subset=['close', 'volume'])
        
        # 按日期升序排序
        df = df.sort_values('date', ascending=True).reset_index(drop=True)
        
        return df
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        計算技術指標
        
        計算指標：
        - MA5, MA10, MA20: 移動平均線
        - Volume_Ratio: 量比（今日成交量 / 5日平均成交量）
        """
        df = df.copy()
        
        # 移動平均線
        df['ma5'] = df['close'].rolling(window=5, min_periods=1).mean()
        df['ma10'] = df['close'].rolling(window=10, min_periods=1).mean()
        df['ma20'] = df['close'].rolling(window=20, min_periods=1).mean()
        
        # 量比：當日成交量 / 5日平均成交量
        # 注意：此處的 volume_ratio 是“日線成交量 / 前5日均量(shift 1)”的相對倍數，
        # 與部分交易軟體口徑的“分時量比（同一時刻對比）”不同，含義更接近“放量倍數”。
        # 該行為目前保留（按需求不改邏輯）。
        avg_volume_5 = df['volume'].rolling(window=5, min_periods=1).mean()
        df['volume_ratio'] = df['volume'] / avg_volume_5.shift(1)
        df['volume_ratio'] = df['volume_ratio'].fillna(1.0)
        
        # 保留2位小數
        for col in ['ma5', 'ma10', 'ma20', 'volume_ratio']:
            if col in df.columns:
                df[col] = df[col].round(2)
        
        return df
    
    @staticmethod
    def random_sleep(min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
        """
        智慧隨機休眠（Jitter）
        
        防封禁策略：模擬人類行為的隨機延遲
        在請求之間加入不規則的等待時間
        """
        sleep_time = random.uniform(min_seconds, max_seconds)
        logger.debug(f"隨機休眠 {sleep_time:.2f} 秒...")
        time.sleep(sleep_time)


class DataFetcherManager:
    """
    資料來源策略管理器
    
    職責：
    1. 管理多個資料來源（按優先順序排序）
    2. 自動故障切換（Failover）
    3. 提供統一的資料獲取介面
    
    切換策略：
    - 優先使用高優先順序資料來源
    - 失敗後自動切換到下一個
    - 所有資料來源都失敗時丟擲異常
    """
    
    def __init__(self, fetchers: Optional[List[BaseFetcher]] = None):
        """
        初始化管理器
        
        Args:
            fetchers: 資料來源列表（可選，預設按優先順序自動建立）
        """
        self._fetchers: List[BaseFetcher] = []
        
        if fetchers:
            # 按優先順序排序
            self._fetchers = sorted(fetchers, key=lambda f: f.priority)
        else:
            # 預設資料來源將在首次使用時延遲載入
            self._init_default_fetchers()
    
    def _init_default_fetchers(self) -> None:
        """Initialize default data sources (US-only: YfinanceFetcher)."""
        from .yfinance_fetcher import YfinanceFetcher

        yfinance = YfinanceFetcher()
        self._fetchers = [yfinance]
        logger.info(f"已初始化 1 個資料來源: YfinanceFetcher(P{yfinance.priority})")
    
    def add_fetcher(self, fetcher: BaseFetcher) -> None:
        """新增資料來源並重新排序"""
        self._fetchers.append(fetcher)
        self._fetchers.sort(key=lambda f: f.priority)
    
    def get_daily_data(
        self,
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: int = 30
    ) -> Tuple[pd.DataFrame, str]:
        """
        獲取日線資料（US stocks via YfinanceFetcher）
        """
        stock_code = normalize_stock_code(stock_code)
        errors = []

        for fetcher in self._fetchers:
            try:
                logger.info(f"[{fetcher.name}] 獲取 {stock_code} 資料...")
                df = fetcher.get_daily_data(
                    stock_code=stock_code,
                    start_date=start_date,
                    end_date=end_date,
                    days=days,
                )
                if df is not None and not df.empty:
                    logger.info(f"[{fetcher.name}] 成功獲取 {stock_code}")
                    return df, fetcher.name
            except Exception as e:
                error_msg = f"[{fetcher.name}] 失敗: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)

        error_summary = f"獲取 {stock_code} 失敗:\n" + "\n".join(errors)
        logger.error(error_summary)
        raise DataFetchError(error_summary)
    
    @property
    def available_fetchers(self) -> List[str]:
        """返回可用資料來源名稱列表"""
        return [f.name for f in self._fetchers]
    
    def prefetch_realtime_quotes(self, stock_codes: List[str]) -> int:
        """批次預取實時行情（US-only: no bulk prefetch needed for yfinance）"""
        return 0
    
    def get_realtime_quote(self, stock_code: str):
        """獲取實時行情（US stocks via YfinanceFetcher）"""
        stock_code = normalize_stock_code(stock_code)

        from src.config import get_config
        config = get_config()

        if not config.enable_realtime_quote:
            logger.debug(f"[實時行情] 功能已禁用，跳過 {stock_code}")
            return None

        for fetcher in self._fetchers:
            if fetcher.name == "YfinanceFetcher" and hasattr(fetcher, 'get_realtime_quote'):
                try:
                    quote = fetcher.get_realtime_quote(stock_code)
                    if quote is not None:
                        logger.info(f"[實時行情] {stock_code} 成功獲取 (來源: yfinance)")
                        return quote
                except Exception as e:
                    logger.warning(f"[實時行情] {stock_code} 獲取失敗: {e}")

        logger.warning(f"[實時行情] {stock_code} 無可用資料來源")
        return None

    def get_chip_distribution(self, stock_code: str):
        """籌碼分佈 — US stocks not supported, always returns None."""
        return None

    def get_stock_name(self, stock_code: str, allow_realtime: bool = True) -> Optional[str]:
        """
        獲取股票中文名稱（自動切換資料來源）
        
        嘗試從多個資料來源獲取股票名稱：
        1. 先從實時行情快取中獲取（如果有）
        2. 依次嘗試各個資料來源的 get_stock_name 方法
        3. 最後嘗試讓大模型透過搜尋獲取（需要外部呼叫）
        
        Args:
            stock_code: 股票程式碼
            allow_realtime: Whether to query realtime quote first. Set False when
                caller only wants lightweight prefetch without triggering heavy
                realtime source calls.
            
        Returns:
            股票中文名稱，所有資料來源都失敗則返回 None
        """
        # Normalize code (strip SH/SZ prefix etc.)
        stock_code = normalize_stock_code(stock_code)
        if stock_code in STOCK_NAME_MAP:
            return STOCK_NAME_MAP[stock_code]

        # 1. 先檢查快取
        if hasattr(self, '_stock_name_cache') and stock_code in self._stock_name_cache:
            return self._stock_name_cache[stock_code]
        
        # 初始化快取
        if not hasattr(self, '_stock_name_cache'):
            self._stock_name_cache = {}
        
        # 2. 嘗試從實時行情中獲取（最快，可按需禁用）
        if allow_realtime:
            quote = self.get_realtime_quote(stock_code)
            if quote and hasattr(quote, 'name') and quote.name:
                name = quote.name
                self._stock_name_cache[stock_code] = name
                logger.info(f"[股票名稱] 從實時行情獲取: {stock_code} -> {name}")
                return name

        # 3. 依次嘗試各個資料來源
        for fetcher in self._fetchers:
            if hasattr(fetcher, 'get_stock_name'):
                try:
                    name = fetcher.get_stock_name(stock_code)
                    if name:
                        self._stock_name_cache[stock_code] = name
                        logger.info(f"[股票名稱] 從 {fetcher.name} 獲取: {stock_code} -> {name}")
                        return name
                except Exception as e:
                    logger.debug(f"[股票名稱] {fetcher.name} 獲取失敗: {e}")
                    continue
        
        # 4. 所有資料來源都失敗
        logger.warning(f"[股票名稱] 所有資料來源都無法獲取 {stock_code} 的名稱")
        return ""

    def prefetch_stock_names(self, stock_codes: List[str], use_bulk: bool = False) -> None:
        """
        Pre-fetch stock names into cache before parallel analysis (Issue #455).

        When use_bulk=False, only calls get_stock_name per code (no get_stock_list),
        avoiding full-market fetch. Sequential execution to avoid rate limits.

        Args:
            stock_codes: Stock codes to prefetch.
            use_bulk: If True, may use get_stock_list (full fetch). Default False.
        """
        if not stock_codes:
            return
        stock_codes = [normalize_stock_code(c) for c in stock_codes]
        if use_bulk:
            self.batch_get_stock_names(stock_codes)
            return
        for code in stock_codes:
            # Skip realtime lookup to avoid triggering expensive full-market quote
            # requests during the prefetch phase.
            self.get_stock_name(code, allow_realtime=False)

    def batch_get_stock_names(self, stock_codes: List[str]) -> Dict[str, str]:
        """
        批次獲取股票中文名稱
        
        先嚐試從支援批次查詢的資料來源獲取股票列表，
        然後再逐個查詢缺失的股票名稱。
        
        Args:
            stock_codes: 股票程式碼列表
            
        Returns:
            {股票程式碼: 股票名稱} 字典
        """
        result = {}
        missing_codes = set(stock_codes)
        
        # 1. 先檢查快取
        if not hasattr(self, '_stock_name_cache'):
            self._stock_name_cache = {}
        
        for code in stock_codes:
            if code in self._stock_name_cache:
                result[code] = self._stock_name_cache[code]
                missing_codes.discard(code)
        
        if not missing_codes:
            return result
        
        # 2. 嘗試批次獲取股票列表
        for fetcher in self._fetchers:
            if hasattr(fetcher, 'get_stock_list') and missing_codes:
                try:
                    stock_list = fetcher.get_stock_list()
                    if stock_list is not None and not stock_list.empty:
                        for _, row in stock_list.iterrows():
                            code = row.get('code')
                            name = row.get('name')
                            if code and name:
                                self._stock_name_cache[code] = name
                                if code in missing_codes:
                                    result[code] = name
                                    missing_codes.discard(code)
                        
                        if not missing_codes:
                            break
                        
                        logger.info(f"[股票名稱] 從 {fetcher.name} 批次獲取完成，剩餘 {len(missing_codes)} 個待查")
                except Exception as e:
                    logger.debug(f"[股票名稱] {fetcher.name} 批次獲取失敗: {e}")
                    continue
        
        # 3. 逐個獲取剩餘的
        for code in list(missing_codes):
            name = self.get_stock_name(code)
            if name:
                result[code] = name
                missing_codes.discard(code)
        
        logger.info(f"[股票名稱] 批次獲取完成，成功 {len(result)}/{len(stock_codes)}")
        return result

    def get_main_indices(self, region: str = "us") -> List[Dict[str, Any]]:
        """獲取主要指數實時行情（自動切換資料來源）"""
        for fetcher in self._fetchers:
            try:
                data = fetcher.get_main_indices(region=region)
                if data:
                    logger.info(f"[{fetcher.name}] 獲取指數行情成功")
                    return data
            except Exception as e:
                logger.warning(f"[{fetcher.name}] 獲取指數行情失敗: {e}")
                continue
        return []

    def get_market_stats(self) -> Dict[str, Any]:
        """獲取市場漲跌統計（自動切換資料來源）"""
        for fetcher in self._fetchers:
            try:
                data = fetcher.get_market_stats()
                if data:
                    logger.info(f"[{fetcher.name}] 獲取市場統計成功")
                    return data
            except Exception as e:
                logger.warning(f"[{fetcher.name}] 獲取市場統計失敗: {e}")
                continue
        return {}

    def get_sector_rankings(self, n: int = 5) -> Tuple[List[Dict], List[Dict]]:
        """獲取板塊漲跌榜（自動切換資料來源）"""
        for fetcher in self._fetchers:
            try:
                data = fetcher.get_sector_rankings(n)
                if data:
                    logger.info(f"[{fetcher.name}] 獲取板塊排行成功")
                    return data
            except Exception as e:
                logger.warning(f"[{fetcher.name}] 獲取板塊排行失敗: {e}")
                continue
        return [], []
