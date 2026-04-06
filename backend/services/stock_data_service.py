"""
股票資料服務
提供真實股票價格抓取與同步功能，支援 yfinance 來源。
"""
import yfinance as yf
from datetime import datetime
from typing import Optional, Dict, Any
import logging

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockDataService:
    """
    股票資料服務架構，支援 yfinance 真實行情抓取。
    """

    @staticmethod
    def _format_stock_code(stock_code: str) -> str:
        """
        格式化股票代碼：若為 4 位純數字則補上 .TW 後綴。
        """
        code = stock_code.strip().upper()
        # 判斷是否為 4 位純數字且不含市場後綴
        if code.isdigit() and len(code) == 4:
            return f"{code}.TW"
        return code

    @classmethod
    def fetch_real_price(cls, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        抓取真實收盤價、日期與成交量。
        若 yfinance 失敗，會回傳 None 以便上層處理。
        """
        formatted_code = cls._format_stock_code(stock_code)
        try:

            ticker = yf.Ticker(formatted_code)
            

            hist = ticker.history(period="5d")
            
            if hist.empty:
                logger.warning(f"無法抓取股票資料: {formatted_code} (查無歷史數據)")
                return None
            
            # 取得最後一筆記錄
            last_row = hist.iloc[-1]
            trade_date = last_row.name.strftime('%Y-%m-%d')
            
            return {
                "stock_code": formatted_code,
                "trade_date": trade_date,
                "open": float(last_row["Open"]) if "Open" in last_row else None,
                "high": float(last_row["High"]) if "High" in last_row else None,
                "low": float(last_row["Low"]) if "Low" in last_row else None,
                "close": float(last_row["Close"]),
                "volume": float(last_row["Volume"]) if "Volume" in last_row else None,
            }
        except Exception as e:
            logger.error(f"抓取股票資料出錯: {formatted_code}, Error: {str(e)}")
            return None

    @classmethod
    def fetch_stock_info(cls, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        從 yfinance 抓取股票的詳細資訊，包含公司名稱。
        """
        formatted_code = cls._format_stock_code(stock_code)
        try:
            ticker = yf.Ticker(formatted_code)
            info = ticker.info
            if not info or len(info) <= 1:
                logger.warning(f"無法抓取股票詳細資訊: {formatted_code} (查無資料)")
                return None
            return info
        except Exception as e:
            logger.error(f"抓取股票詳細資訊出錯: {formatted_code}, Error: {str(e)}")
            return None

