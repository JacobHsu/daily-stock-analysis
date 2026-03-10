// 生產環境使用相對路徑（同源），開發環境使用環境變數或預設本地地址
export const API_BASE_URL = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? '' : 'http://127.0.0.1:8000');
