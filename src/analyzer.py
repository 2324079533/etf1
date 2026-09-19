import json
from openai import OpenAI
from src.config import config

ETF_ANALYSIS_PROMPT = """你是一名资深的大类资产配置与量化 ETF 策略投资专家。
请对提供的 ETF 多维量化与基本面信息进行专业、客观的投资研判。

注意：这是【ETF 指数基金】而非个股，严禁使用个股财报/业绩来分析！必须从宏观环境、标的指数、折溢价率风险、大类资产轮动与定投价值切入。

输入数据如下：
标的代码: {code} ({name})
最新价: {price} (日涨跌幅: {change}%)
折溢价率: {premium_rate}
均线状态: {trend_ma} | MA20: {ma20} | MA60: {ma60}
14日RSI: {rsi_14} | 年化波动率: {volatility}%
参考网格区间: {grid_suggest}

请严格按以下 JSON 结构输出，勿带任何 Markdown 额外标记：
{{
  "etf_code": "{code}",
  "etf_name": "{name}",
  "stance": "强力买入 / 逢低定投 / 观望持有 / 逢高减仓 / 卖出回避",
  "score": 0到100的综合评分,
  "premium_risk": "高溢价预警 / 处于安全合理区间 / 折价具备安全边际",
  "macro_and_sector": "一句话概括宏观经济周期与该标的板块当前所处阶段",
  "technical_verdict": "技术面趋势与超买超卖评估",
  "strategy_advice": "具体的建仓、定投或网格交易执行建议",
  "risk_warning": "最大潜在风险点"
}}
"""

class ETFAnalyzer:
    def __init__(self):
        self.client = OpenAI(
            api_key=config.llm_api_key,
            base_url=config.llm_base_url
        )

    def analyze(self, etf_data: dict) -> dict:
        tech = etf_data.get("technical", {})
        prompt = ETF_ANALYSIS_PROMPT.format(
            code=etf_data["code"],
            name=etf_data["name"],
            price=tech.get("latest_price", "N/A"),
            change=tech.get("change_pct", 0.0),
            premium_rate=etf_data.get("premium_rate", "0.0%"),
            trend_ma=tech.get("trend_ma", "未知"),
            ma20=tech.get("ma20", "N/A"),
            ma60=tech.get("ma60", "N/A"),
            rsi_14=tech.get("rsi_14", "N/A"),
            volatility=tech.get("volatility_annual_pct", "N/A"),
            grid_suggest=tech.get("grid_suggest", "N/A")
        )
        try:
            response = self.client.chat.completions.create(
                model=config.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {
                "etf_code": etf_data["code"],
                "etf_name": etf_data["name"],
                "stance": "分析异常",
                "score": 50,
                "premium_risk": "未知",
                "macro_and_sector": "模型调用失败",
                "technical_verdict": "无",
                "strategy_advice": str(e),
                "risk_warning": "请检查配置"
            }
