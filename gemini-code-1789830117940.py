import akshare as ak
import yfinance as yf
import pandas as pd
from typing import Dict, Any
from src.indicators import calculate_technical_indicators

class ETFDataFetcher:
    @staticmethod
    def get_etf_info(code: str) -> Dict[str, Any]:
        code = str(code).strip()
        data = {
            "code": code,
            "name": code,
            "premium_rate": "0.00%",
            "top_holdings": [],
            "technical": {}
        }
        
        # A 股 ETF 处理
        if code.isdigit() and len(code) == 6:
            try:
                spot_df = ak.fund_etf_spot_em()
                matched = spot_df[spot_df['代码'] == code]
                if not matched.empty:
                    row = matched.iloc[0]
                    data["name"] = row.get("名称", code)
                    data["premium_rate"] = f"{row.get('折价率', '0.00')}%"
                
                hist_df = ak.fund_etf_hist_em(symbol=code, period="daily", adjust="qfq")
                if not hist_df.empty:
                    hist_df = hist_df.rename(columns={"收盘": "close", "开盘": "open", "最高": "high", "最低": "low"})
                    data["technical"] = calculate_technical_indicators(hist_df.tail(120))
            except Exception as e:
                print(f"[{code}] 数据抓取提示: {e}")
        else:
            # 美股/全球 ETF 处理
            try:
                ticker = yf.Ticker(code)
                hist = ticker.history(period="6mo")
                if not hist.empty:
                    hist = hist.reset_index().rename(columns={"Close": "close", "Open": "open", "High": "high", "Low": "low"})
                    data["technical"] = calculate_technical_indicators(hist)
                data["name"] = ticker.info.get("shortName", code)
            except Exception as e:
                print(f"[{code}] 全球 ETF 提示: {e}")

        return data