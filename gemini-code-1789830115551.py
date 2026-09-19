import pandas as pd
import numpy as np

def calculate_technical_indicators(df: pd.DataFrame) -> dict:
    if df.empty or len(df) < 20:
        return {}

    close = df['close']
    ma5 = close.rolling(5).mean().iloc[-1]
    ma20 = close.rolling(20).mean().iloc[-1]
    ma60 = close.rolling(60).mean().iloc[-1] if len(df) >= 60 else None
    
    # RSI (14)
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    rsi_14 = (100 - (100 / (1 + rs))).iloc[-1]

    # 年化波动率
    returns = np.log(close / close.shift(1))
    volatility = returns.rolling(20).std().iloc[-1] * np.sqrt(252) * 100
    
    latest_close = close.iloc[-1]
    return {
        "latest_price": latest_close,
        "change_pct": round(((latest_close - df['close'].iloc[-2]) / df['close'].iloc[-2]) * 100, 2),
        "ma5": round(ma5, 4),
        "ma20": round(ma20, 4),
        "ma60": round(ma60, 4) if ma60 is not None else "N/A",
        "trend_ma": "多头排列" if ma5 > ma20 and (ma60 is None or ma20 > ma60) else "震荡/空头",
        "rsi_14": round(rsi_14, 2),
        "volatility_annual_pct": round(volatility, 2) if not np.isnan(volatility) else 0.0,
        "grid_suggest": f"[{round(latest_close * 0.97, 4)} ~ {round(latest_close * 1.03, 4)}]"
    }