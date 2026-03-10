# -*- coding: utf-8 -*-
"""
===================================
自選股智能分析系統 - 核心分析流水線
===================================

職責：
1. 管理整個分析流程
2. 協調資料取得、儲存、搜索、分析、通知等模組
3. 實作並發控制和例外處理
4. 提供股票分析的核心功能
"""

import logging
import time
import uuid
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

from src.config import get_config, Config
from src.storage import get_db
from data_provider import DataFetcherManager
from data_provider.realtime_types import ChipDistribution
from src.analyzer import GeminiAnalyzer, AnalysisResult, STOCK_NAME_MAP
from src.notification import NotificationService, NotificationChannel
from src.search_service import SearchService
from src.enums import ReportType
from src.stock_analyzer import StockTrendAnalyzer, TrendAnalysisResult
from src.core.trading_calendar import get_market_for_stock, is_market_open
from bot.models import BotMessage


logger = logging.getLogger(__name__)


class StockAnalysisPipeline:
    """
    股票分析主流程調度器

    職責：
    1. 管理整個分析流程
    2. 協調資料取得、儲存、搜索、分析、通知等模組
    3. 實作並發控制和例外處理
    """
    
    def __init__(
        self,
        config: Optional[Config] = None,
        max_workers: Optional[int] = None,
        source_message: Optional[BotMessage] = None,
        query_id: Optional[str] = None,
        query_source: Optional[str] = None,
        save_context_snapshot: Optional[bool] = None
    ):
        """
        初始化調度器

        Args:
            config: 配置物件（可選，預設使用全域配置）
            max_workers: 最大並發執行緒數（可選，預設從配置讀取）
        """
        self.config = config or get_config()
        self.max_workers = max_workers or self.config.max_workers
        self.source_message = source_message
        self.query_id = query_id
        self.query_source = self._resolve_query_source(query_source)
        self.save_context_snapshot = (
            self.config.save_context_snapshot if save_context_snapshot is None else save_context_snapshot
        )
        
        # 初始化各模組
        self.db = get_db()
        self.fetcher_manager = DataFetcherManager()
        self.trend_analyzer = StockTrendAnalyzer()  # 趨勢分析器
        self.analyzer = GeminiAnalyzer()
        self.notifier = NotificationService(source_message=source_message)

        # 初始化搜索服務
        self.search_service = SearchService(
            bocha_keys=self.config.bocha_api_keys,
            tavily_keys=self.config.tavily_api_keys,
            brave_keys=self.config.brave_api_keys,
            serpapi_keys=self.config.serpapi_keys,
            news_max_age_days=self.config.news_max_age_days,
        )
        
        logger.info(f"調度器初始化完成，最大並發數: {self.max_workers}")
        logger.info("已啟用趨勢分析器 (MA5>MA10>MA20 多頭判斷)")
        # 列印即時行情/籌碼配置狀態
        if self.config.enable_realtime_quote:
            logger.info(f"即時行情已啟用 (優先級: {self.config.realtime_source_priority})")
        else:
            logger.info("即時行情已禁用，將使用歷史收盤價")
        if self.config.enable_chip_distribution:
            logger.info("籌碼分布分析已啟用")
        else:
            logger.info("籌碼分布分析已禁用")
        if self.search_service.is_available:
            logger.info("搜索服務已啟用 (Tavily/SerpAPI)")
        else:
            logger.warning("搜索服務未啟用（未配置 API Key）")
    
    def fetch_and_save_stock_data(
        self, 
        code: str,
        force_refresh: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        取得並儲存單支股票資料

        斷點續傳邏輯：
        1. 檢查資料庫是否已有今日資料
        2. 如果有且不強制刷新，則跳過網路請求
        3. 否則從資料來源取得並儲存

        Args:
            code: 股票代碼
            force_refresh: 是否強制刷新（忽略本地快取）

        Returns:
            Tuple[是否成功, 錯誤資訊]
        """
        try:
            # 首先取得股票名稱
            stock_name = self.fetcher_manager.get_stock_name(code)

            today = date.today()
            # 注意：這裡用自然日 date.today() 做「斷點續傳」判斷。
            # 若在週末/節假日/非交易日運行，或機器時區不在中國，可能出現：
            # - 資料庫已有最新交易日資料但仍會重複拉取（has_today_data 回傳 False）
            # - 或在跨日/時區偏移時誤判「今日已有資料」
            # 該行為目前保留（按需求不改邏輯），但如需更嚴謹可改為「最新交易日/資料來源最新日期」判斷。

            # 斷點續傳檢查：如果今日資料已存在，跳過
            if not force_refresh and self.db.has_today_data(code, today):
                logger.info(f"{stock_name}({code}) 今日資料已存在，跳過取得（斷點續傳）")
                return True, None

            # 從資料來源取得資料
            logger.info(f"{stock_name}({code}) 開始從資料來源取得資料...")
            df, source_name = self.fetcher_manager.get_daily_data(code, days=30)

            if df is None or df.empty:
                return False, "取得資料為空"

            # 儲存到資料庫
            saved_count = self.db.save_daily_data(df, code, source_name)
            logger.info(f"{stock_name}({code}) 資料儲存成功（來源: {source_name}，新增 {saved_count} 筆）")

            return True, None

        except Exception as e:
            error_msg = f"取得/儲存資料失敗: {str(e)}"
            logger.error(f"{stock_name}({code}) {error_msg}")
            return False, error_msg
    
    def analyze_stock(self, code: str, report_type: ReportType, query_id: str) -> Optional[AnalysisResult]:
        """
        分析單支股票（增強版：含量比、換手率、籌碼分析、多維度情報）

        流程：
        1. 取得即時行情（量比、換手率）- 透過 DataFetcherManager 自動故障切換
        2. 取得籌碼分布 - 透過 DataFetcherManager 帶熔斷保護
        3. 進行趨勢分析（基於交易理念）
        4. 多維度情報搜索（最新消息+風險排查+業績預期）
        5. 從資料庫取得分析上下文
        6. 呼叫 AI 進行綜合分析

        Args:
            query_id: 查詢鏈路關聯 id
            code: 股票代碼
            report_type: 報告類型

        Returns:
            AnalysisResult 或 None（如果分析失敗）
        """
        try:
            # 取得股票名稱（優先從即時行情取得真實名稱）
            stock_name = self.fetcher_manager.get_stock_name(code)

            # Step 1: 取得即時行情（量比、換手率等）- 使用統一入口，自動故障切換
            realtime_quote = None
            try:
                realtime_quote = self.fetcher_manager.get_realtime_quote(code)
                if realtime_quote:
                    # 使用即時行情回傳的真實股票名稱
                    if realtime_quote.name:
                        stock_name = realtime_quote.name
                    # 相容不同資料來源的欄位（有些資料來源可能沒有 volume_ratio）
                    volume_ratio = getattr(realtime_quote, 'volume_ratio', None)
                    turnover_rate = getattr(realtime_quote, 'turnover_rate', None)
                    logger.info(f"{stock_name}({code}) 即時行情: 價格={realtime_quote.price}, "
                              f"量比={volume_ratio}, 換手率={turnover_rate}% "
                              f"(來源: {realtime_quote.source.value if hasattr(realtime_quote, 'source') else 'unknown'})")
                else:
                    logger.info(f"{stock_name}({code}) 即時行情取得失敗或已禁用，將使用歷史資料進行分析")
            except Exception as e:
                logger.warning(f"{stock_name}({code}) 取得即時行情失敗: {e}")

            # 如果還是沒有名稱，使用代碼作為名稱
            if not stock_name:
                stock_name = f'股票{code}'

            # Step 2: 取得籌碼分布 - 使用統一入口，帶熔斷保護
            chip_data = None
            try:
                chip_data = self.fetcher_manager.get_chip_distribution(code)
                if chip_data:
                    logger.info(f"{stock_name}({code}) 籌碼分布: 獲利比例={chip_data.profit_ratio:.1%}, "
                              f"90%集中度={chip_data.concentration_90:.2%}")
                else:
                    logger.debug(f"{stock_name}({code}) 籌碼分布取得失敗或已禁用")
            except Exception as e:
                logger.warning(f"{stock_name}({code}) 取得籌碼分布失敗: {e}")

            # If agent mode is enabled, or specific agent skills are configured, use the Agent analysis pipeline
            use_agent = getattr(self.config, 'agent_mode', False)
            if not use_agent:
                # Auto-enable agent mode when specific skills are configured (e.g., scheduled task with strategy)
                configured_skills = getattr(self.config, 'agent_skills', [])
                if configured_skills and configured_skills != ['all']:
                    use_agent = True
                    logger.info(f"{stock_name}({code}) Auto-enabled agent mode due to configured skills: {configured_skills}")

            if use_agent:
                logger.info(f"{stock_name}({code}) 啟用 Agent 模式進行分析")
                return self._analyze_with_agent(code, report_type, query_id, stock_name, realtime_quote, chip_data)

            # Step 3: 趨勢分析（基於交易理念）
            trend_result: Optional[TrendAnalysisResult] = None
            try:
                end_date = date.today()
                start_date = end_date - timedelta(days=89)  # ~60 trading days for MA60
                historical_bars = self.db.get_data_range(code, start_date, end_date)
                if historical_bars:
                    df = pd.DataFrame([bar.to_dict() for bar in historical_bars])
                    # Issue #234: Augment with realtime for intraday MA calculation
                    if self.config.enable_realtime_quote and realtime_quote:
                        df = self._augment_historical_with_realtime(df, realtime_quote, code)
                    trend_result = self.trend_analyzer.analyze(df, code)
                    logger.info(f"{stock_name}({code}) 趨勢分析: {trend_result.trend_status.value}, "
                              f"買入訊號={trend_result.buy_signal.value}, 評分={trend_result.signal_score}")
            except Exception as e:
                logger.warning(f"{stock_name}({code}) 趨勢分析失敗: {e}", exc_info=True)

            # Step 4: 多維度情報搜索（最新消息+風險排查+業績預期）
            news_context = None
            if self.search_service.is_available:
                logger.info(f"{stock_name}({code}) 開始多維度情報搜索...")

                # 使用多維度搜索（最多5次搜索）
                intel_results = self.search_service.search_comprehensive_intel(
                    stock_code=code,
                    stock_name=stock_name,
                    max_searches=5
                )

                # 格式化情報報告
                if intel_results:
                    news_context = self.search_service.format_intel_report(intel_results, stock_name)
                    total_results = sum(
                        len(r.results) for r in intel_results.values() if r.success
                    )
                    logger.info(f"{stock_name}({code}) 情報搜索完成: 共 {total_results} 筆結果")
                    logger.debug(f"{stock_name}({code}) 情報搜索結果:\n{news_context}")

                    # 儲存新聞情報到資料庫（用於後續復盤與查詢）
                    try:
                        query_context = self._build_query_context(query_id=query_id)
                        for dim_name, response in intel_results.items():
                            if response and response.success and response.results:
                                self.db.save_news_intel(
                                    code=code,
                                    name=stock_name,
                                    dimension=dim_name,
                                    query=response.query,
                                    response=response,
                                    query_context=query_context
                                )
                    except Exception as e:
                        logger.warning(f"{stock_name}({code}) 儲存新聞情報失敗: {e}")
            else:
                logger.info(f"{stock_name}({code}) 搜索服務不可用，跳過情報搜索")

            # Step 5: 取得分析上下文（技術面資料）
            context = self.db.get_analysis_context(code)

            if context is None:
                logger.warning(f"{stock_name}({code}) 無法取得歷史行情資料，將僅基於新聞和即時行情分析")
                context = {
                    'code': code,
                    'stock_name': stock_name,
                    'date': date.today().isoformat(),
                    'data_missing': True,
                    'today': {},
                    'yesterday': {}
                }
            
            # Step 6: 增強上下文資料（添加即時行情、籌碼、趨勢分析結果、股票名稱）
            enhanced_context = self._enhance_context(
                context,
                realtime_quote,
                chip_data,
                trend_result,
                stock_name  # 傳入股票名稱
            )

            # Step 7: 呼叫 AI 分析（傳入增強的上下文和新聞）
            result = self.analyzer.analyze(enhanced_context, news_context=news_context)

            # Step 7.5: 填充分析時的價格資訊到 result
            if result:
                realtime_data = enhanced_context.get('realtime', {})
                result.current_price = realtime_data.get('price')
                result.change_pct = realtime_data.get('change_pct')

            # Step 8: 儲存分析歷史記錄
            if result:
                try:
                    context_snapshot = self._build_context_snapshot(
                        enhanced_context=enhanced_context,
                        news_content=news_context,
                        realtime_quote=realtime_quote,
                        chip_data=chip_data
                    )
                    self.db.save_analysis_history(
                        result=result,
                        query_id=query_id,
                        report_type=report_type.value,
                        news_content=news_context,
                        context_snapshot=context_snapshot,
                        save_snapshot=self.save_context_snapshot
                    )
                except Exception as e:
                    logger.warning(f"{stock_name}({code}) 儲存分析歷史失敗: {e}")

            return result

        except Exception as e:
            logger.error(f"{stock_name}({code}) 分析失敗: {e}")
            logger.exception(f"{stock_name}({code}) 詳細錯誤資訊:")
            return None
    
    def _enhance_context(
        self,
        context: Dict[str, Any],
        realtime_quote,
        chip_data: Optional[ChipDistribution],
        trend_result: Optional[TrendAnalysisResult],
        stock_name: str = ""
    ) -> Dict[str, Any]:
        """
        增強分析上下文

        將即時行情、籌碼分布、趨勢分析結果、股票名稱添加到上下文中

        Args:
            context: 原始上下文
            realtime_quote: 即時行情資料（UnifiedRealtimeQuote 或 None）
            chip_data: 籌碼分布資料
            trend_result: 趨勢分析結果
            stock_name: 股票名稱

        Returns:
            增強後的上下文
        """
        enhanced = context.copy()
        
        # 添加股票名稱
        if stock_name:
            enhanced['stock_name'] = stock_name
        elif realtime_quote and getattr(realtime_quote, 'name', None):
            enhanced['stock_name'] = realtime_quote.name

        # 添加即時行情（相容不同資料來源的欄位差異）
        if realtime_quote:
            # 使用 getattr 安全取得欄位，缺失欄位回傳 None 或預設值
            volume_ratio = getattr(realtime_quote, 'volume_ratio', None)
            enhanced['realtime'] = {
                'name': getattr(realtime_quote, 'name', ''),
                'price': getattr(realtime_quote, 'price', None),
                'change_pct': getattr(realtime_quote, 'change_pct', None),
                'volume_ratio': volume_ratio,
                'volume_ratio_desc': self._describe_volume_ratio(volume_ratio) if volume_ratio else '無資料',
                'turnover_rate': getattr(realtime_quote, 'turnover_rate', None),
                'pe_ratio': getattr(realtime_quote, 'pe_ratio', None),
                'pb_ratio': getattr(realtime_quote, 'pb_ratio', None),
                'total_mv': getattr(realtime_quote, 'total_mv', None),
                'circ_mv': getattr(realtime_quote, 'circ_mv', None),
                'change_60d': getattr(realtime_quote, 'change_60d', None),
                'source': getattr(realtime_quote, 'source', None),
            }
            # 移除 None 值以減少上下文大小
            enhanced['realtime'] = {k: v for k, v in enhanced['realtime'].items() if v is not None}

        # 添加籌碼分布
        if chip_data:
            current_price = getattr(realtime_quote, 'price', 0) if realtime_quote else 0
            enhanced['chip'] = {
                'profit_ratio': chip_data.profit_ratio,
                'avg_cost': chip_data.avg_cost,
                'concentration_90': chip_data.concentration_90,
                'concentration_70': chip_data.concentration_70,
                'chip_status': chip_data.get_chip_status(current_price or 0),
            }

        # 添加趨勢分析結果
        if trend_result:
            enhanced['trend_analysis'] = {
                'trend_status': trend_result.trend_status.value,
                'ma_alignment': trend_result.ma_alignment,
                'trend_strength': trend_result.trend_strength,
                'bias_ma5': trend_result.bias_ma5,
                'bias_ma10': trend_result.bias_ma10,
                'volume_status': trend_result.volume_status.value,
                'volume_trend': trend_result.volume_trend,
                'buy_signal': trend_result.buy_signal.value,
                'signal_score': trend_result.signal_score,
                'signal_reasons': trend_result.signal_reasons,
                'risk_factors': trend_result.risk_factors,
            }

        # Issue #234: Override today with realtime OHLC + trend MA for intraday analysis
        # Guard: trend_result.ma5 > 0 ensures MA calculation succeeded (data sufficient)
        if realtime_quote and trend_result and trend_result.ma5 > 0:
            price = getattr(realtime_quote, 'price', None)
            if price is not None and price > 0:
                yesterday_close = None
                if enhanced.get('yesterday') and isinstance(enhanced['yesterday'], dict):
                    yesterday_close = enhanced['yesterday'].get('close')
                orig_today = enhanced.get('today') or {}
                open_p = getattr(realtime_quote, 'open_price', None) or getattr(
                    realtime_quote, 'pre_close', None
                ) or yesterday_close or orig_today.get('open') or price
                high_p = getattr(realtime_quote, 'high', None) or price
                low_p = getattr(realtime_quote, 'low', None) or price
                vol = getattr(realtime_quote, 'volume', None)
                amt = getattr(realtime_quote, 'amount', None)
                pct = getattr(realtime_quote, 'change_pct', None)
                realtime_today = {
                    'close': price,
                    'open': open_p,
                    'high': high_p,
                    'low': low_p,
                    'ma5': trend_result.ma5,
                    'ma10': trend_result.ma10,
                    'ma20': trend_result.ma20,
                }
                if vol is not None:
                    realtime_today['volume'] = vol
                if amt is not None:
                    realtime_today['amount'] = amt
                if pct is not None:
                    realtime_today['pct_chg'] = pct
                for k, v in orig_today.items():
                    if k not in realtime_today and v is not None:
                        realtime_today[k] = v
                enhanced['today'] = realtime_today
                enhanced['ma_status'] = self._compute_ma_status(
                    price, trend_result.ma5, trend_result.ma10, trend_result.ma20
                )
                enhanced['date'] = date.today().isoformat()
                if yesterday_close is not None:
                    try:
                        yc = float(yesterday_close)
                        if yc > 0:
                            enhanced['price_change_ratio'] = round(
                                (price - yc) / yc * 100, 2
                            )
                    except (TypeError, ValueError):
                        pass
                if vol is not None and enhanced.get('yesterday'):
                    yest_vol = enhanced['yesterday'].get('volume') if isinstance(
                        enhanced['yesterday'], dict
                    ) else None
                    if yest_vol is not None:
                        try:
                            yv = float(yest_vol)
                            if yv > 0:
                                enhanced['volume_change_ratio'] = round(
                                    float(vol) / yv, 2
                                )
                        except (TypeError, ValueError):
                            pass

        # ETF/index flag for analyzer prompt (Fixes #274)
        enhanced['is_index_etf'] = SearchService.is_index_or_etf(
            context.get('code', ''), enhanced.get('stock_name', stock_name)
        )

        return enhanced

    def _analyze_with_agent(
        self,
        code: str,
        report_type: ReportType,
        query_id: str,
        stock_name: str,
        realtime_quote: Any,
        chip_data: Optional[ChipDistribution]
    ) -> Optional[AnalysisResult]:
        """
        使用 Agent 模式分析單支股票。
        """
        try:
            from src.agent.factory import build_agent_executor

            # Build executor from shared factory (ToolRegistry and SkillManager prototype are cached)
            executor = build_agent_executor(self.config, getattr(self.config, 'agent_skills', None) or None)

            # Build initial context to avoid redundant tool calls
            initial_context = {
                "stock_code": code,
                "stock_name": stock_name,
                "report_type": report_type.value,
            }
            
            if realtime_quote:
                initial_context["realtime_quote"] = self._safe_to_dict(realtime_quote)
            if chip_data:
                initial_context["chip_distribution"] = self._safe_to_dict(chip_data)

            # 運行 Agent
            message = f"請分析股票 {code} ({stock_name})，並生成決策儀表板報告。"
            agent_result = executor.run(message, context=initial_context)

            # 轉換為 AnalysisResult
            result = self._agent_result_to_analysis_result(agent_result, code, stock_name, report_type, query_id)
            resolved_stock_name = result.name if result and result.name else stock_name

            # 儲存新聞情報到資料庫（Agent 工具結果僅用於 LLM 上下文，未持久化，Fixes #396）
            # 使用 search_stock_news（與 Agent 工具呼叫邏輯一致），僅 1 次 API 呼叫，無額外延遲
            if self.search_service.is_available:
                try:
                    news_response = self.search_service.search_stock_news(
                        stock_code=code,
                        stock_name=resolved_stock_name,
                        max_results=5
                    )
                    if news_response.success and news_response.results:
                        query_context = self._build_query_context(query_id=query_id)
                        self.db.save_news_intel(
                            code=code,
                            name=resolved_stock_name,
                            dimension="latest_news",
                            query=news_response.query,
                            response=news_response,
                            query_context=query_context
                        )
                        logger.info(f"[{code}] Agent 模式: 新聞情報已儲存 {len(news_response.results)} 筆")
                except Exception as e:
                    logger.warning(f"[{code}] Agent 模式儲存新聞情報失敗: {e}")

            # 儲存分析歷史記錄
            if result:
                try:
                    initial_context["stock_name"] = resolved_stock_name
                    self.db.save_analysis_history(
                        result=result,
                        query_id=query_id,
                        report_type=report_type.value,
                        news_content=None,
                        context_snapshot=initial_context,
                        save_snapshot=self.save_context_snapshot
                    )
                except Exception as e:
                    logger.warning(f"[{code}] 儲存 Agent 分析歷史失敗: {e}")

            return result

        except Exception as e:
            logger.error(f"[{code}] Agent 分析失敗: {e}")
            logger.exception(f"[{code}] Agent 詳細錯誤資訊:")
            return None

    def _agent_result_to_analysis_result(
        self, agent_result, code: str, stock_name: str, report_type: ReportType, query_id: str
    ) -> AnalysisResult:
        """
        將 AgentResult 轉換為 AnalysisResult。
        """
        result = AnalysisResult(
            code=code,
            name=stock_name,
            sentiment_score=50,
            trend_prediction="未知",
            operation_advice="觀望",
            success=agent_result.success,
            error_message=agent_result.error if not agent_result.success else None,
            data_sources=f"agent:{agent_result.provider}",
            model_used=agent_result.model or None,
        )

        if agent_result.success and agent_result.dashboard:
            dash = agent_result.dashboard
            ai_stock_name = str(dash.get("stock_name", "")).strip()
            if ai_stock_name and self._is_placeholder_stock_name(stock_name, code):
                result.name = ai_stock_name
            result.sentiment_score = self._safe_int(dash.get("sentiment_score"), 50)
            result.trend_prediction = dash.get("trend_prediction", "未知")
            result.operation_advice = dash.get("operation_advice", "觀望")
            result.decision_type = dash.get("decision_type", "hold")
            result.analysis_summary = dash.get("analysis_summary", "")
            # The AI returns a top-level dict that contains a nested 'dashboard' sub-key
            # with core_conclusion / battle_plan / intelligence.  AnalysisResult's helper
            # methods (get_sniper_points, get_core_conclusion, etc.) expect that inner
            # structure, so we unwrap it here.
            result.dashboard = dash.get("dashboard") or dash
        else:
            result.sentiment_score = 50
            result.operation_advice = "觀望"
            if not result.error_message:
                result.error_message = "Agent 未能生成有效的決策儀表板"

        return result

    @staticmethod
    def _is_placeholder_stock_name(name: str, code: str) -> bool:
        """Return True when the stock name is missing or placeholder-like."""
        if not name:
            return True
        normalized = str(name).strip()
        if not normalized:
            return True
        if normalized == code:
            return True
        if normalized.startswith("股票"):
            return True
        if "Unknown" in normalized:
            return True
        return False

    @staticmethod
    def _safe_int(value: Any, default: int = 50) -> int:
        """安全地將值轉換為整數。"""
        if value is None:
            return default
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            import re
            match = re.search(r'-?\d+', value)
            if match:
                return int(match.group())
        return default
    
    def _describe_volume_ratio(self, volume_ratio: float) -> str:
        """
        量比描述

        量比 = 當前成交量 / 過去5日平均成交量
        """
        if volume_ratio < 0.5:
            return "極度萎縮"
        elif volume_ratio < 0.8:
            return "明顯萎縮"
        elif volume_ratio < 1.2:
            return "正常"
        elif volume_ratio < 2.0:
            return "溫和放量"
        elif volume_ratio < 3.0:
            return "明顯放量"
        else:
            return "巨量"

    @staticmethod
    def _compute_ma_status(close: float, ma5: float, ma10: float, ma20: float) -> str:
        """
        Compute MA alignment status from price and MA values.
        Logic mirrors storage._analyze_ma_status (Issue #234).
        """
        close = close or 0
        ma5 = ma5 or 0
        ma10 = ma10 or 0
        ma20 = ma20 or 0
        if close > ma5 > ma10 > ma20 > 0:
            return "多頭排列 📈"
        elif close < ma5 < ma10 < ma20 and ma20 > 0:
            return "空頭排列 📉"
        elif close > ma5 and ma5 > ma10:
            return "短期向好 🔼"
        elif close < ma5 and ma5 < ma10:
            return "短期走弱 🔽"
        else:
            return "震盪整理 ↔️"

    def _augment_historical_with_realtime(
        self, df: pd.DataFrame, realtime_quote: Any, code: str
    ) -> pd.DataFrame:
        """
        Augment historical OHLCV with today's realtime quote for intraday MA calculation.
        Issue #234: Use realtime price instead of yesterday's close for technical indicators.
        """
        if df is None or df.empty or 'close' not in df.columns:
            return df
        if realtime_quote is None:
            return df
        price = getattr(realtime_quote, 'price', None)
        if price is None or not (isinstance(price, (int, float)) and price > 0):
            return df

        # Optional: skip augmentation on non-trading days (fail-open)
        enable_realtime_tech = getattr(
            self.config, 'enable_realtime_technical_indicators', True
        )
        if not enable_realtime_tech:
            return df
        market = get_market_for_stock(code)
        if market and not is_market_open(market, date.today()):
            return df

        last_val = df['date'].max()
        last_date = (
            last_val.date() if hasattr(last_val, 'date') else
            (last_val if isinstance(last_val, date) else pd.Timestamp(last_val).date())
        )
        yesterday_close = float(df.iloc[-1]['close']) if len(df) > 0 else price
        open_p = getattr(realtime_quote, 'open_price', None) or getattr(
            realtime_quote, 'pre_close', None
        ) or yesterday_close
        high_p = getattr(realtime_quote, 'high', None) or price
        low_p = getattr(realtime_quote, 'low', None) or price
        vol = getattr(realtime_quote, 'volume', None) or 0
        amt = getattr(realtime_quote, 'amount', None)
        pct = getattr(realtime_quote, 'change_pct', None)

        if last_date >= date.today():
            # Update last row with realtime close (copy to avoid mutating caller's df)
            df = df.copy()
            idx = df.index[-1]
            df.loc[idx, 'close'] = price
            if open_p is not None:
                df.loc[idx, 'open'] = open_p
            if high_p is not None:
                df.loc[idx, 'high'] = high_p
            if low_p is not None:
                df.loc[idx, 'low'] = low_p
            if vol:
                df.loc[idx, 'volume'] = vol
            if amt is not None:
                df.loc[idx, 'amount'] = amt
            if pct is not None:
                df.loc[idx, 'pct_chg'] = pct
        else:
            # Append virtual today row
            new_row = {
                'code': code,
                'date': date.today(),
                'open': open_p,
                'high': high_p,
                'low': low_p,
                'close': price,
                'volume': vol,
                'amount': amt if amt is not None else 0,
                'pct_chg': pct if pct is not None else 0,
            }
            new_df = pd.DataFrame([new_row])
            df = pd.concat([df, new_df], ignore_index=True)
        return df

    def _build_context_snapshot(
        self,
        enhanced_context: Dict[str, Any],
        news_content: Optional[str],
        realtime_quote: Any,
        chip_data: Optional[ChipDistribution]
    ) -> Dict[str, Any]:
        """
        建立分析上下文快照
        """
        return {
            "enhanced_context": enhanced_context,
            "news_content": news_content,
            "realtime_quote_raw": self._safe_to_dict(realtime_quote),
            "chip_distribution_raw": self._safe_to_dict(chip_data),
        }

    @staticmethod
    def _safe_to_dict(value: Any) -> Optional[Dict[str, Any]]:
        """
        安全轉換為字典
        """
        if value is None:
            return None
        if hasattr(value, "to_dict"):
            try:
                return value.to_dict()
            except Exception:
                return None
        if hasattr(value, "__dict__"):
            try:
                return dict(value.__dict__)
            except Exception:
                return None
        return None

    def _resolve_query_source(self, query_source: Optional[str]) -> str:
        """
        解析請求來源。

        優先級（從高到低）：
        1. 顯式傳入的 query_source：呼叫方明確指定時優先使用，便於覆蓋推斷結果或相容未來 source_message 來自非 bot 的場景
        2. 存在 source_message 時推斷為 "bot"：當前約定為機器人會話上下文
        3. 存在 query_id 時推斷為 "web"：Web 觸發的請求會帶上 query_id
        4. 預設 "system"：定時任務或 CLI 等無上述上下文時

        Args:
            query_source: 呼叫方顯式指定的來源，如 "bot" / "web" / "cli" / "system"

        Returns:
            歸一化後的來源標識字串，如 "bot" / "web" / "cli" / "system"
        """
        if query_source:
            return query_source
        if self.source_message:
            return "bot"
        if self.query_id:
            return "web"
        return "system"

    def _build_query_context(self, query_id: Optional[str] = None) -> Dict[str, str]:
        """
        生成使用者查詢關聯資訊
        """
        effective_query_id = query_id or self.query_id or ""

        context: Dict[str, str] = {
            "query_id": effective_query_id,
            "query_source": self.query_source or "",
        }

        if self.source_message:
            context.update({
                "requester_platform": self.source_message.platform or "",
                "requester_user_id": self.source_message.user_id or "",
                "requester_user_name": self.source_message.user_name or "",
                "requester_chat_id": self.source_message.chat_id or "",
                "requester_message_id": self.source_message.message_id or "",
                "requester_query": self.source_message.content or "",
            })

        return context
    
    def process_single_stock(
        self,
        code: str,
        skip_analysis: bool = False,
        single_stock_notify: bool = False,
        report_type: ReportType = ReportType.SIMPLE,
        analysis_query_id: Optional[str] = None,
    ) -> Optional[AnalysisResult]:
        """
        處理單支股票的完整流程

        包括：
        1. 取得資料
        2. 儲存資料
        3. AI 分析
        4. 單股推送（可選，#55）

        此方法會被執行緒池呼叫，需要處理好例外

        Args:
            analysis_query_id: 查詢鏈路關聯 id
            code: 股票代碼
            skip_analysis: 是否跳過 AI 分析
            single_stock_notify: 是否啟用單股推送模式（每分析完一支立即推送）
            report_type: 報告類型列舉（從配置讀取，Issue #119）

        Returns:
            AnalysisResult 或 None
        """
        logger.info(f"========== 開始處理 {code} ==========")

        try:
            # Step 1: 取得並儲存資料
            success, error = self.fetch_and_save_stock_data(code)

            if not success:
                logger.warning(f"[{code}] 資料取得失敗: {error}")
                # 即使取得失敗，也嘗試用已有資料分析

            # Step 2: AI 分析
            if skip_analysis:
                logger.info(f"[{code}] 跳過 AI 分析（dry-run 模式）")
                return None
            
            effective_query_id = analysis_query_id or self.query_id or uuid.uuid4().hex
            result = self.analyze_stock(code, report_type, query_id=effective_query_id)
            
            if result:
                logger.info(
                    f"[{code}] 分析完成: {result.operation_advice}, "
                    f"評分 {result.sentiment_score}"
                )

                # 單股推送模式（#55）：每分析完一支股票立即推送（AI 失敗時跳過）
                if single_stock_notify and self.notifier.is_available() and getattr(result, 'success', True):
                    try:
                        # 根據報告類型選擇生成方法
                        if report_type == ReportType.FULL:
                            # 完整報告：使用決策儀表板格式
                            report_content = self.notifier.generate_dashboard_report([result])
                            logger.info(f"[{code}] 使用完整報告格式")
                        else:
                            # 精簡報告：使用單股報告格式（預設）
                            report_content = self.notifier.generate_single_stock_report(result)
                            logger.info(f"[{code}] 使用精簡報告格式")

                        if self.notifier.send(report_content, email_stock_codes=[code]):
                            logger.info(f"[{code}] 單股推送成功")
                        else:
                            logger.warning(f"[{code}] 單股推送失敗")
                    except Exception as e:
                        logger.error(f"[{code}] 單股推送例外: {e}")

            return result

        except Exception as e:
            # 捕獲所有例外，確保單股失敗不影響整體
            logger.exception(f"[{code}] 處理過程發生未知例外: {e}")
            return None
    
    def run(
        self,
        stock_codes: Optional[List[str]] = None,
        dry_run: bool = False,
        send_notification: bool = True,
        merge_notification: bool = False
    ) -> List[AnalysisResult]:
        """
        運行完整的分析流程

        流程：
        1. 取得待分析的股票列表
        2. 使用執行緒池並發處理
        3. 收集分析結果
        4. 發送通知

        Args:
            stock_codes: 股票代碼列表（可選，預設使用配置中的自選股）
            dry_run: 是否僅取得資料不分析
            send_notification: 是否發送推送通知
            merge_notification: 是否合併推送（跳過本次推送，由 main 層合併個股+大盤後統一發送，Issue #190）

        Returns:
            分析結果列表
        """
        start_time = time.time()
        
        # 使用配置中的股票列表
        if stock_codes is None:
            self.config.refresh_stock_list()
            stock_codes = self.config.stock_list
        
        if not stock_codes:
            logger.error("未配置自選股列表，請在 .env 檔案中設定 STOCK_LIST")
            return []

        logger.info(f"===== 開始分析 {len(stock_codes)} 支股票 =====")
        logger.info(f"股票列表: {', '.join(stock_codes)}")
        logger.info(f"並發數: {self.max_workers}, 模式: {'僅取得資料' if dry_run else '完整分析'}")

        # === 批次預取即時行情（優化：避免每支股票都觸發全量拉取）===
        # 只有股票數量 >= 5 時才進行預取，少量股票直接逐個查詢更高效
        if len(stock_codes) >= 5:
            prefetch_count = self.fetcher_manager.prefetch_realtime_quotes(stock_codes)
            if prefetch_count > 0:
                logger.info(f"已啟用批次預取架構：一次拉取全市場資料，{len(stock_codes)} 支股票共享快取")

        # Issue #455: 預取股票名稱，避免並發分析時顯示「股票xxxxx」
        # dry_run 僅做資料拉取，不需要名稱預取，避免額外網路開銷
        if not dry_run:
            self.fetcher_manager.prefetch_stock_names(stock_codes, use_bulk=False)

        # 單股推送模式（#55）：從配置讀取
        single_stock_notify = getattr(self.config, 'single_stock_notify', False)
        # Issue #119: 從配置讀取報告類型
        report_type_str = getattr(self.config, 'report_type', 'simple').lower()
        report_type = ReportType.FULL if report_type_str == 'full' else ReportType.SIMPLE
        # Issue #128: 從配置讀取分析間隔
        analysis_delay = getattr(self.config, 'analysis_delay', 0)

        if single_stock_notify:
            logger.info(f"已啟用單股推送模式：每分析完一支股票立即推送（報告類型: {report_type_str}）")
        
        results: List[AnalysisResult] = []

        # 使用執行緒池並發處理
        # 注意：max_workers 設定較低（預設3）以避免觸發反爬
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交任務
            future_to_code = {
                executor.submit(
                    self.process_single_stock,
                    code,
                    skip_analysis=dry_run,
                    single_stock_notify=single_stock_notify and send_notification,
                    report_type=report_type,  # Issue #119: 傳遞報告類型
                    analysis_query_id=uuid.uuid4().hex,
                ): code
                for code in stock_codes
            }

            # 收集結果
            for idx, future in enumerate(as_completed(future_to_code)):
                code = future_to_code[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)

                    # Issue #128: 分析間隔 - 在個股分析和大盤分析之間添加延遲
                    if idx < len(stock_codes) - 1 and analysis_delay > 0:
                        # 注意：此 sleep 發生在「主執行緒收集 future 的迴圈」中，
                        # 並不會阻止執行緒池中的任務同時發起網路請求。
                        # 因此它對降低並發請求峰值的效果有限；真正的峰值主要由 max_workers 決定。
                        # 該行為目前保留（按需求不改邏輯）。
                        logger.debug(f"等待 {analysis_delay} 秒後繼續下一支股票...")
                        time.sleep(analysis_delay)

                except Exception as e:
                    logger.error(f"[{code}] 任務執行失敗: {e}")

        # 統計
        elapsed_time = time.time() - start_time

        # dry-run 模式下，資料取得成功即視為成功
        if dry_run:
            # 檢查哪些股票的資料今天已存在
            success_count = sum(1 for code in stock_codes if self.db.has_today_data(code))
            fail_count = len(stock_codes) - success_count
        else:
            success_count = len(results)
            fail_count = len(stock_codes) - success_count

        logger.info("===== 分析完成 =====")
        logger.info(f"成功: {success_count}, 失敗: {fail_count}, 耗時: {elapsed_time:.2f} 秒")

        # 發送通知（單股推送模式下跳過彙總推送，避免重複）
        # 如果所有結果都是 AI 失敗（success=False），跳過推送
        ai_success_results = [r for r in results if getattr(r, 'success', True)]
        if not ai_success_results and results:
            logger.warning("所有股票 AI 分析均失敗，跳過推送通知")
            return results
        if results and send_notification and not dry_run:
            if single_stock_notify:
                # 單股推送模式：只儲存彙總報告，不再重複推送
                logger.info("單股推送模式：跳過彙總推送，僅儲存報告到本地")
                self._send_notifications(results, skip_push=True)
            elif merge_notification:
                # 合併模式（Issue #190）：僅儲存，不推送，由 main 層合併個股+大盤復盤後統一發送
                logger.info("合併推送模式：跳過本次推送，將在個股+大盤復盤後統一發送")
                self._send_notifications(results, skip_push=True)
            else:
                self._send_notifications(results)
        
        return results
    
    def _send_notifications(self, results: List[AnalysisResult], skip_push: bool = False) -> None:
        """
        發送分析結果通知

        生成決策儀表板格式的報告

        Args:
            results: 分析結果列表
            skip_push: 是否跳過推送（僅儲存到本地，用於單股推送模式）
        """
        try:
            logger.info("生成決策儀表板日報...")

            # 生成決策儀表板格式的詳細日報
            report = self.notifier.generate_dashboard_report(results)

            # 儲存到本地
            filepath = self.notifier.save_report_to_file(report)
            logger.info(f"決策儀表板日報已儲存: {filepath}")

            # 跳過推送（單股推送模式）
            if skip_push:
                return

            # 推送通知
            if self.notifier.is_available():
                channels = self.notifier.get_available_channels()
                context_success = self.notifier.send_to_context(report)

                # Issue #455: Markdown 转图片（与 notification.send 逻辑一致）
                from src.md2img import markdown_to_image

                channels_needing_image = {
                    ch for ch in channels
                    if ch.value in self.notifier._markdown_to_image_channels
                }

                def _get_md2img_hint() -> str:
                    try:
                        engine = getattr(get_config(), "md2img_engine", "wkhtmltoimage")
                    except Exception:
                        engine = "wkhtmltoimage"
                    return (
                        "npm i -g markdown-to-file" if engine == "markdown-to-file"
                        else "wkhtmltopdf (apt install wkhtmltopdf / brew install wkhtmltopdf)"
                    )

                image_bytes = None
                if channels_needing_image:
                    image_bytes = markdown_to_image(
                        report, max_chars=self.notifier._markdown_to_image_max_chars
                    )
                    if image_bytes:
                        logger.info(
                            "Markdown 已轉換為圖片，將向 %s 發送圖片",
                            [ch.value for ch in channels_needing_image],
                        )
                    else:
                        logger.warning(
                            "Markdown 轉圖片失敗，將回退為文字發送。請檢查 MARKDOWN_TO_IMAGE_CHANNELS 配置並安裝 %s",
                            _get_md2img_hint(),
                        )

                # 其他渠道：發完整報告
                non_wechat_success = False
                stock_email_groups = getattr(self.config, 'stock_email_groups', []) or []
                for channel in channels:
                    if channel == NotificationChannel.TELEGRAM:
                        use_image = self.notifier._should_use_image_for_channel(
                            channel, image_bytes
                        )
                        if use_image:
                            result = self.notifier._send_telegram_photo(image_bytes)
                        else:
                            result = self.notifier.send_to_telegram(report)
                        non_wechat_success = result or non_wechat_success
                    elif channel == NotificationChannel.EMAIL:
                        if stock_email_groups:
                            code_to_emails: Dict[str, Optional[List[str]]] = {}
                            for r in results:
                                if r.code not in code_to_emails:
                                    emails = []
                                    for stocks, emails_list in stock_email_groups:
                                        if r.code in stocks:
                                            emails.extend(emails_list)
                                    code_to_emails[r.code] = list(dict.fromkeys(emails)) if emails else None
                            emails_to_results: Dict[Optional[Tuple], List] = defaultdict(list)
                            for r in results:
                                recs = code_to_emails.get(r.code)
                                key = tuple(recs) if recs else None
                                emails_to_results[key].append(r)
                            for key, group_results in emails_to_results.items():
                                grp_report = self.notifier.generate_dashboard_report(group_results)
                                grp_image_bytes = None
                                if channel.value in self.notifier._markdown_to_image_channels:
                                    grp_image_bytes = markdown_to_image(
                                        grp_report,
                                        max_chars=self.notifier._markdown_to_image_max_chars,
                                    )
                                use_image = self.notifier._should_use_image_for_channel(
                                    channel, grp_image_bytes
                                )
                                receivers = list(key) if key is not None else None
                                if use_image:
                                    result = self.notifier._send_email_with_inline_image(
                                        grp_image_bytes, receivers=receivers
                                    )
                                else:
                                    result = self.notifier.send_to_email(
                                        grp_report, receivers=receivers
                                    )
                                non_wechat_success = result or non_wechat_success
                        else:
                            use_image = self.notifier._should_use_image_for_channel(
                                channel, image_bytes
                            )
                            if use_image:
                                result = self.notifier._send_email_with_inline_image(image_bytes)
                            else:
                                result = self.notifier.send_to_email(report)
                            non_wechat_success = result or non_wechat_success
                    elif channel == NotificationChannel.CUSTOM:
                        use_image = self.notifier._should_use_image_for_channel(
                            channel, image_bytes
                        )
                        if use_image:
                            result = self.notifier._send_custom_webhook_image(
                                image_bytes, fallback_content=report
                            )
                        else:
                            result = self.notifier.send_to_custom(report)
                        non_wechat_success = result or non_wechat_success
                    elif channel == NotificationChannel.DISCORD:
                        non_wechat_success = self.notifier.send_to_discord(report) or non_wechat_success
                    elif channel == NotificationChannel.PUSHOVER:
                        non_wechat_success = self.notifier.send_to_pushover(report) or non_wechat_success
                    elif channel == NotificationChannel.ASTRBOT:
                        non_wechat_success = self.notifier.send_to_astrbot(report) or non_wechat_success
                    else:
                        logger.warning(f"未知通知渠道: {channel}")

                success = non_wechat_success or context_success
                if success:
                    logger.info("決策儀表板推送成功")
                else:
                    logger.warning("決策儀表板推送失敗")
            else:
                logger.info("通知渠道未配置，跳過推送")

        except Exception as e:
            logger.error(f"發送通知失敗: {e}")
