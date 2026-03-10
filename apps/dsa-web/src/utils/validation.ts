interface ValidationResult {
  valid: boolean;
  message?: string;
  normalized: string;
}

// 美股常見程式碼格式的基礎校驗
export const validateStockCode = (value: string): ValidationResult => {
  const normalized = value.trim().toUpperCase();

  if (!normalized) {
    return { valid: false, message: '請輸入股票程式碼', normalized };
  }

  const patterns = [
    /^[A-Z]{1,5}$/, // 美股 Ticker（1-5 位大寫字母）
    /^[A-Z]{1,6}(\.[A-Z]{1,2})?$/, // 美股含字尾（如 BRK.A）
  ];

  const valid = patterns.some((regex) => regex.test(normalized));

  return {
    valid,
    message: valid ? undefined : '股票程式碼格式不正確',
    normalized,
  };
};
