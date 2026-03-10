import type { SystemConfigCategory } from '../types/systemConfig';

const categoryTitleMap: Record<SystemConfigCategory, string> = {
  base: '基礎設定',
  data_source: '資料來源',
  ai_model: 'AI 模型',
  notification: '通知渠道',
  system: '系統設定',
  agent: 'Agent 設定',
  backtest: '回測配置',
  uncategorized: '其他',
};

const categoryDescriptionMap: Partial<Record<SystemConfigCategory, string>> = {
  base: '管理自選股與基礎執行引數。',
  data_source: '管理行情資料來源與優先順序策略。',
  ai_model: '管理模型供應商、模型名稱與推理引數。',
  notification: '管理機器人、Webhook 和訊息推送配置。',
  system: '管理排程、日誌、埠等系統級引數。',
  agent: '管理 Agent 模式、技能與策略配置。',
  backtest: '管理回測開關、評估視窗和引擎引數。',
  uncategorized: '其他未歸類的配置項。',
};

const fieldTitleMap: Record<string, string> = {
  STOCK_LIST: '自選股列表',
  TUSHARE_TOKEN: 'Tushare Token',
  TAVILY_API_KEYS: 'Tavily API Keys',
  SERPAPI_API_KEYS: 'SerpAPI API Keys',
  BRAVE_API_KEYS: 'Brave API Keys',
  REALTIME_SOURCE_PRIORITY: '實時資料來源優先順序',
  ENABLE_REALTIME_TECHNICAL_INDICATORS: '盤中實時技術面',
  LITELLM_MODEL: '主模型',
  LITELLM_FALLBACK_MODELS: '備選模型',
  LITELLM_CONFIG: 'LiteLLM 配置檔案',
  LLM_CHANNELS: 'LLM 渠道列表',
  AIHUBMIX_KEY: 'AIHubmix Key',
  DEEPSEEK_API_KEY: 'DeepSeek API Key',
  GEMINI_API_KEY: 'Gemini API Key',
  GEMINI_MODEL: 'Gemini 模型',
  GEMINI_TEMPERATURE: 'Gemini 溫度引數',
  OPENAI_API_KEY: 'OpenAI API Key',
  OPENAI_BASE_URL: 'OpenAI Base URL',
  OPENAI_MODEL: 'OpenAI 模型',
  WECHAT_WEBHOOK_URL: '企業微信 Webhook',
  PUSHPLUS_TOKEN: 'PushPlus Token',
  REPORT_SUMMARY_ONLY: '僅分析結果摘要',
  SCHEDULE_TIME: '定時任務時間',
  HTTP_PROXY: 'HTTP 代理',
  LOG_LEVEL: '日誌級別',
  WEBUI_PORT: 'WebUI 埠',
  AGENT_MODE: '啟用 Agent 模式',
  AGENT_MAX_STEPS: 'Agent 最大步數',
  AGENT_SKILLS: 'Agent 啟用技能',
  AGENT_STRATEGY_DIR: 'Agent 策略目錄',
  BACKTEST_ENABLED: '啟用回測',
  BACKTEST_EVAL_WINDOW_DAYS: '回測評估視窗（交易日）',
  BACKTEST_MIN_AGE_DAYS: '回測最小歷史天數',
  BACKTEST_ENGINE_VERSION: '回測引擎版本',
  BACKTEST_NEUTRAL_BAND_PCT: '回測中性區間閾值（%）',
};

const fieldDescriptionMap: Record<string, string> = {
  STOCK_LIST: '使用逗號分隔股票程式碼，例如：AAPL,TSLA。',
  TUSHARE_TOKEN: '用於接入 Tushare Pro 資料服務的憑據。',
  TAVILY_API_KEYS: '用於新聞檢索的 Tavily 金鑰，支援逗號分隔多個。',
  SERPAPI_API_KEYS: '用於新聞檢索的 SerpAPI 金鑰，支援逗號分隔多個。',
  BRAVE_API_KEYS: '用於新聞檢索的 Brave Search 金鑰，支援逗號分隔多個。',
  REALTIME_SOURCE_PRIORITY: '按逗號分隔填寫資料來源呼叫優先順序。',
  ENABLE_REALTIME_TECHNICAL_INDICATORS: '盤中分析時用實時價計算 MA5/MA10/MA20 與多頭排列（Issue #234）；關閉則用昨日收盤。',
  LITELLM_MODEL: '主模型，格式 provider/model（如 gemini/gemini-2.5-flash）。配置渠道後自動推斷。',
  LITELLM_FALLBACK_MODELS: '備選模型，逗號分隔，主模型失敗時按序嘗試。',
  LITELLM_CONFIG: 'LiteLLM YAML 配置檔案路徑（高階用法），優先順序最高。',
  LLM_CHANNELS: '渠道名稱列表（逗號分隔）。推薦使用上方渠道編輯器管理。',
  AIHUBMIX_KEY: 'AIHubmix 一站式金鑰，自動指向 aihubmix.com/v1。',
  DEEPSEEK_API_KEY: 'DeepSeek 官方 API 金鑰。填寫後自動使用 deepseek-chat 模型。',
  GEMINI_API_KEY: '用於 Gemini 服務呼叫的金鑰。',
  GEMINI_MODEL: '設定 Gemini 分析模型名稱。',
  GEMINI_TEMPERATURE: '控制模型輸出隨機性，範圍通常為 0.0 到 2.0。',
  OPENAI_API_KEY: '用於 OpenAI 相容服務呼叫的金鑰。',
  OPENAI_BASE_URL: 'OpenAI 相容 API 地址，例如 https://api.deepseek.com/v1。',
  OPENAI_MODEL: 'OpenAI 相容模型名稱，例如 gpt-4o-mini、deepseek-chat。',
  WECHAT_WEBHOOK_URL: '企業微信機器人 Webhook 地址。',
  PUSHPLUS_TOKEN: 'PushPlus 推送令牌。',
  REPORT_SUMMARY_ONLY: '僅推送分析結果摘要，不包含個股詳情。多股時適合快速瀏覽。',
  SCHEDULE_TIME: '每日定時任務執行時間，格式為 HH:MM。',
  HTTP_PROXY: '網路代理地址，可留空。',
  LOG_LEVEL: '設定日誌輸出級別。',
  WEBUI_PORT: 'Web 頁面服務監聽埠。',
  AGENT_MODE: '是否啟用 ReAct Agent 進行股票分析。',
  AGENT_MAX_STEPS: 'Agent 思考和呼叫工具的最大步數。',
  AGENT_SKILLS: '逗號分隔的啟用技能/策略列表，例如：trend_following,value_investing。',
  AGENT_STRATEGY_DIR: '存放 Agent 策略 YAML 檔案的目錄路徑。',
  BACKTEST_ENABLED: '是否啟用回測功能（true/false）。',
  BACKTEST_EVAL_WINDOW_DAYS: '回測評估視窗長度，單位為交易日。',
  BACKTEST_MIN_AGE_DAYS: '僅回測早於該天數的分析記錄。',
  BACKTEST_ENGINE_VERSION: '回測引擎版本標識，用於區分結果版本。',
  BACKTEST_NEUTRAL_BAND_PCT: '中性區間閾值百分比，例如 2 表示 -2%~+2%。',
};

export function getCategoryTitleZh(category: SystemConfigCategory, fallback?: string): string {
  return categoryTitleMap[category] || fallback || category;
}

export function getCategoryDescriptionZh(category: SystemConfigCategory, fallback?: string): string {
  return categoryDescriptionMap[category] || fallback || '';
}

export function getFieldTitleZh(key: string, fallback?: string): string {
  return fieldTitleMap[key] || fallback || key;
}

export function getFieldDescriptionZh(key: string, fallback?: string): string {
  return fieldDescriptionMap[key] || fallback || '';
}
