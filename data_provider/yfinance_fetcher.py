# -*- coding: utf-8 -*-
"""
===================================
YfinanceFetcher - 美股資料來源 (Priority 4)
===================================

資料來源：Yahoo Finance（透過 yfinance 庫）
支援：美股股票（AAPL、TSLA）與美股指數（SPX、DJI 等）

關鍵策略：
1. 處理 Yahoo Finance 的資料格式差異
2. 失敗後指數退避重試
"""

import logging
import re
from datetime import datetime
from typing import Optional, List, Dict, Any

import pandas as pd
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from .base import BaseFetcher, DataFetchError, STANDARD_COLUMNS
from .realtime_types import UnifiedRealtimeQuote, RealtimeSource
from .us_index_mapping import get_us_index_yf_symbol, is_us_index_code, is_us_stock_code
import os

logger = logging.getLogger(__name__)


class YfinanceFetcher(BaseFetcher):
    """
    Yahoo Finance 資料來源實現

    資料來源：Yahoo Finance
    支援：美股股票（AAPL、TSLA）與美股指數（SPX、DJI 等）

    關鍵策略：
    - 處理時區和資料格式差異
    - 失敗後指數退避重試
    """
    
    name = "YfinanceFetcher"
    priority = int(os.getenv("YFINANCE_PRIORITY", "4"))
    
    def __init__(self):
        """初始化 YfinanceFetcher"""
        pass
    
    def _convert_stock_code(self, stock_code: str) -> str:
        """
        轉換股票程式碼為 Yahoo Finance 格式

        Yahoo Finance 程式碼格式：
        - 美股：AAPL, TSLA, GOOGL（無需字尾）
        - 美股指數：SPX -> ^GSPC

        Args:
            stock_code: 原始程式碼，如 'AAPL', 'SPX'

        Returns:
            Yahoo Finance 格式程式碼

        Examples:
            >>> fetcher._convert_stock_code('AAPL')
            'AAPL'
            >>> fetcher._convert_stock_code('SPX')
            '^GSPC'
        """
        code = stock_code.strip().upper()

        # 美股指數：對映到 Yahoo Finance 符號（如 SPX -> ^GSPC）
        yf_symbol, _ = get_us_index_yf_symbol(code)
        if yf_symbol:
            logger.debug(f"識別為美股指數: {code} -> {yf_symbol}")
            return yf_symbol

        # 美股：1-5 個大寫字母（可選 .X 字尾），原樣返回
        if is_us_stock_code(code):
            logger.debug(f"識別為美股程式碼: {code}")
            return code

        logger.warning(f"無法識別股票程式碼 {code}，原樣返回")
        return code
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        從 Yahoo Finance 獲取原始資料
        
        使用 yfinance.download() 獲取歷史資料
        
        流程：
        1. 轉換股票程式碼格式
        2. 呼叫 yfinance API
        3. 處理返回資料
        """
        import yfinance as yf
        
        # 轉換程式碼格式
        yf_code = self._convert_stock_code(stock_code)
        
        logger.debug(f"呼叫 yfinance.download({yf_code}, {start_date}, {end_date})")
        
        try:
            # 使用 yfinance 下載資料
            df = yf.download(
                tickers=yf_code,
                start=start_date,
                end=end_date,
                progress=False,  # 禁止進度條
                auto_adjust=True,  # 自動調整價格（復權）
                multi_level_index=True
            )
            
            # 篩選出 yf_code 的列, 避免多隻股票資料混淆
            if isinstance(df.columns, pd.MultiIndex) and len(df.columns) > 1:
                ticker_level = df.columns.get_level_values(1)
                mask = ticker_level == yf_code
                if mask.any():
                    df = df.loc[:, mask].copy()
                
            if df.empty:
                raise DataFetchError(f"Yahoo Finance 未查詢到 {stock_code} 的資料")
            
            return df
            
        except Exception as e:
            if isinstance(e, DataFetchError):
                raise
            raise DataFetchError(f"Yahoo Finance 獲取資料失敗: {e}") from e
    
    def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """
        標準化 Yahoo Finance 資料
        
        yfinance 返回的列名：
        Open, High, Low, Close, Volume（索引是日期）
        
        注意：新版 yfinance 返回 MultiIndex 列名，如 ('Close', 'AMD')
        需要先扁平化列名再進行處理
        
        需要對映到標準列名：
        date, open, high, low, close, volume, amount, pct_chg
        """
        df = df.copy()
        
        # 處理 MultiIndex 列名（新版 yfinance 返回格式）
        # 例如: ('Close', 'AMD') -> 'Close'
        if isinstance(df.columns, pd.MultiIndex):
            logger.debug(f"檢測到 MultiIndex 列名，進行扁平化處理")
            # 取第一級列名（Price level: Close, High, Low, etc.）
            df.columns = df.columns.get_level_values(0)
        
        # 重置索引，將日期從索引變為列
        df = df.reset_index()
        
        # 列名對映（yfinance 使用首字母大寫）
        column_mapping = {
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume',
        }
        
        df = df.rename(columns=column_mapping)
        
        # 計算漲跌幅（因為 yfinance 不直接提供）
        if 'close' in df.columns:
            df['pct_chg'] = df['close'].pct_change() * 100
            df['pct_chg'] = df['pct_chg'].fillna(0).round(2)
        
        # 計算成交額（yfinance 不提供，使用估算值）
        # 成交額 ≈ 成交量 * 平均價格
        if 'volume' in df.columns and 'close' in df.columns:
            df['amount'] = df['volume'] * df['close']
        else:
            df['amount'] = 0
        
        # 新增股票程式碼列
        df['code'] = stock_code
        
        # 只保留需要的列
        keep_cols = ['code'] + STANDARD_COLUMNS
        existing_cols = [col for col in keep_cols if col in df.columns]
        df = df[existing_cols]
        
        return df

    def _fetch_yf_ticker_data(self, yf, yf_code: str, name: str, return_code: str) -> Optional[Dict[str, Any]]:
        """
        透過 yfinance 拉取單個指數/股票的行情資料。

        Args:
            yf: yfinance 模組引用
            yf_code: yfinance 使用的程式碼（如 '^GSPC'、'AAPL'）
            name: 指數顯示名稱
            return_code: 寫入結果 dict 的 code 欄位（如 'SPX'）

        Returns:
            行情字典，失敗時返回 None
        """
        ticker = yf.Ticker(yf_code)
        # 取近兩日資料以計算漲跌幅
        hist = ticker.history(period='2d')
        if hist.empty:
            return None
        today_row = hist.iloc[-1]
        prev_row = hist.iloc[-2] if len(hist) > 1 else today_row
        price = float(today_row['Close'])
        prev_close = float(prev_row['Close'])
        change = price - prev_close
        change_pct = (change / prev_close) * 100 if prev_close else 0
        high = float(today_row['High'])
        low = float(today_row['Low'])
        # 振幅 = (最高 - 最低) / 昨收 * 100
        amplitude = ((high - low) / prev_close * 100) if prev_close else 0
        return {
            'code': return_code,
            'name': name,
            'current': price,
            'change': change,
            'change_pct': change_pct,
            'open': float(today_row['Open']),
            'high': high,
            'low': low,
            'prev_close': prev_close,
            'volume': float(today_row['Volume']),
            'amount': 0.0,  # Yahoo Finance 不提供準確成交額
            'amplitude': amplitude,
        }

    def get_main_indices(self, region: str = "us") -> Optional[List[Dict[str, Any]]]:
        """獲取美股主要指數行情 (Yahoo Finance)。"""
        import yfinance as yf
        return self._get_us_main_indices(yf)

    def _get_us_main_indices(self, yf) -> Optional[List[Dict[str, Any]]]:
        """獲取美股主要指數行情（SPX、IXIC、DJI、VIX），複用 _fetch_yf_ticker_data"""
        # 大盤覆盤所需核心美股指數
        us_indices = ['SPX', 'IXIC', 'DJI', 'VIX']
        results = []
        try:
            for code in us_indices:
                yf_symbol, name = get_us_index_yf_symbol(code)
                if not yf_symbol:
                    continue
                try:
                    item = self._fetch_yf_ticker_data(yf, yf_symbol, name, code)
                    if item:
                        results.append(item)
                        logger.debug(f"[Yfinance] 獲取美股指數 {name} 成功")
                except Exception as e:
                    logger.warning(f"[Yfinance] 獲取美股指數 {name} 失敗: {e}")

            if results:
                logger.info(f"[Yfinance] 成功獲取 {len(results)} 個美股指數行情")
                return results

        except Exception as e:
            logger.error(f"[Yfinance] 獲取美股指數行情失敗: {e}")

        return None

    def _is_us_stock(self, stock_code: str) -> bool:
        """
        判斷程式碼是否為美股股票（排除美股指數）。

        委託給 us_index_mapping 模組的 is_us_stock_code()。
        """
        return is_us_stock_code(stock_code)

    def _get_us_index_realtime_quote(
        self,
        user_code: str,
        yf_symbol: str,
        index_name: str,
    ) -> Optional[UnifiedRealtimeQuote]:
        """
        Get realtime quote for US index (e.g. SPX -> ^GSPC).

        Args:
            user_code: User input code (e.g. SPX)
            yf_symbol: Yahoo Finance symbol (e.g. ^GSPC)
            index_name: Chinese name for the index

        Returns:
            UnifiedRealtimeQuote or None
        """
        import yfinance as yf

        try:
            logger.debug(f"[Yfinance] 獲取美股指數 {user_code} ({yf_symbol}) 實時行情")
            ticker = yf.Ticker(yf_symbol)

            try:
                info = ticker.fast_info
                if info is None:
                    raise ValueError("fast_info is None")
                price = getattr(info, 'lastPrice', None) or getattr(info, 'last_price', None)
                prev_close = getattr(info, 'previousClose', None) or getattr(info, 'previous_close', None)
                open_price = getattr(info, 'open', None)
                high = getattr(info, 'dayHigh', None) or getattr(info, 'day_high', None)
                low = getattr(info, 'dayLow', None) or getattr(info, 'day_low', None)
                volume = getattr(info, 'lastVolume', None) or getattr(info, 'last_volume', None)
            except Exception:
                logger.debug(f"[Yfinance] fast_info 失敗，嘗試 history 方法")
                hist = ticker.history(period='2d')
                if hist.empty:
                    logger.warning(f"[Yfinance] 無法獲取 {yf_symbol} 的資料")
                    return None
                today = hist.iloc[-1]
                prev = hist.iloc[-2] if len(hist) > 1 else today
                price = float(today['Close'])
                prev_close = float(prev['Close'])
                open_price = float(today['Open'])
                high = float(today['High'])
                low = float(today['Low'])
                volume = int(today['Volume'])

            change_amount = None
            change_pct = None
            if price is not None and prev_close is not None and prev_close > 0:
                change_amount = price - prev_close
                change_pct = (change_amount / prev_close) * 100

            amplitude = None
            if high is not None and low is not None and prev_close is not None and prev_close > 0:
                amplitude = ((high - low) / prev_close) * 100

            quote = UnifiedRealtimeQuote(
                code=user_code,
                name=index_name or user_code,
                source=RealtimeSource.FALLBACK,
                price=price,
                change_pct=round(change_pct, 2) if change_pct is not None else None,
                change_amount=round(change_amount, 4) if change_amount is not None else None,
                volume=volume,
                amount=None,
                volume_ratio=None,
                turnover_rate=None,
                amplitude=round(amplitude, 2) if amplitude is not None else None,
                open_price=open_price,
                high=high,
                low=low,
                pre_close=prev_close,
                pe_ratio=None,
                pb_ratio=None,
                total_mv=None,
                circ_mv=None,
            )
            logger.info(f"[Yfinance] 獲取美股指數 {user_code} 實時行情成功: 價格={price}")
            return quote
        except Exception as e:
            logger.warning(f"[Yfinance] 獲取美股指數 {user_code} 實時行情失敗: {e}")
            return None

    def get_realtime_quote(self, stock_code: str) -> Optional[UnifiedRealtimeQuote]:
        """
        獲取美股/美股指數實時行情資料

        支援美股股票（AAPL、TSLA）和美股指數（SPX、DJI 等）。
        資料來源：yfinance Ticker.info

        Args:
            stock_code: 美股程式碼或指數程式碼，如 'AMD', 'AAPL', 'SPX', 'DJI'

        Returns:
            UnifiedRealtimeQuote 物件，獲取失敗返回 None
        """
        import yfinance as yf

        # 美股指數：使用對映（SPX -> ^GSPC）
        yf_symbol, index_name = get_us_index_yf_symbol(stock_code)
        if yf_symbol:
            return self._get_us_index_realtime_quote(
                user_code=stock_code.strip().upper(),
                yf_symbol=yf_symbol,
                index_name=index_name,
            )

        # 僅處理美股股票
        if not self._is_us_stock(stock_code):
            logger.debug(f"[Yfinance] {stock_code} 不是美股，跳過")
            return None

        try:
            symbol = stock_code.strip().upper()
            logger.debug(f"[Yfinance] 獲取美股 {symbol} 實時行情")
            
            ticker = yf.Ticker(symbol)
            
            # 嘗試獲取 fast_info（更快，但欄位較少）
            try:
                info = ticker.fast_info
                if info is None:
                    raise ValueError("fast_info is None")
                
                price = getattr(info, 'lastPrice', None) or getattr(info, 'last_price', None)
                prev_close = getattr(info, 'previousClose', None) or getattr(info, 'previous_close', None)
                open_price = getattr(info, 'open', None)
                high = getattr(info, 'dayHigh', None) or getattr(info, 'day_high', None)
                low = getattr(info, 'dayLow', None) or getattr(info, 'day_low', None)
                volume = getattr(info, 'lastVolume', None) or getattr(info, 'last_volume', None)
                market_cap = getattr(info, 'marketCap', None) or getattr(info, 'market_cap', None)
                
            except Exception:
                # 回退到 history 方法獲取最新資料
                logger.debug(f"[Yfinance] fast_info 失敗，嘗試 history 方法")
                hist = ticker.history(period='2d')
                if hist.empty:
                    logger.warning(f"[Yfinance] 無法獲取 {symbol} 的資料")
                    return None
                
                today = hist.iloc[-1]
                prev = hist.iloc[-2] if len(hist) > 1 else today
                
                price = float(today['Close'])
                prev_close = float(prev['Close'])
                open_price = float(today['Open'])
                high = float(today['High'])
                low = float(today['Low'])
                volume = int(today['Volume'])
                market_cap = None
            
            # 計算漲跌幅
            change_amount = None
            change_pct = None
            if price is not None and prev_close is not None and prev_close > 0:
                change_amount = price - prev_close
                change_pct = (change_amount / prev_close) * 100
            
            # 計算振幅
            amplitude = None
            if high is not None and low is not None and prev_close is not None and prev_close > 0:
                amplitude = ((high - low) / prev_close) * 100
            
            # 獲取股票名稱
            try:
                name = ticker.info.get('shortName', '') or ticker.info.get('longName', '') or symbol
            except Exception:
                name = symbol
            
            quote = UnifiedRealtimeQuote(
                code=symbol,
                name=name,
                source=RealtimeSource.FALLBACK,
                price=price,
                change_pct=round(change_pct, 2) if change_pct is not None else None,
                change_amount=round(change_amount, 4) if change_amount is not None else None,
                volume=volume,
                amount=None,  # yfinance 不直接提供成交額
                volume_ratio=None,
                turnover_rate=None,
                amplitude=round(amplitude, 2) if amplitude is not None else None,
                open_price=open_price,
                high=high,
                low=low,
                pre_close=prev_close,
                pe_ratio=None,
                pb_ratio=None,
                total_mv=market_cap,
                circ_mv=None,
            )
            
            logger.info(f"[Yfinance] 獲取美股 {symbol} 實時行情成功: 價格={price}")
            return quote
            
        except Exception as e:
            logger.warning(f"[Yfinance] 獲取美股 {stock_code} 實時行情失敗: {e}")
            return None


if __name__ == "__main__":
    # 測試程式碼
    logging.basicConfig(level=logging.DEBUG)

    fetcher = YfinanceFetcher()

    try:
        df = fetcher.get_daily_data('AAPL')
        print(f"獲取成功，共 {len(df)} 條資料")
        print(df.tail())
    except Exception as e:
        print(f"獲取失敗: {e}")
