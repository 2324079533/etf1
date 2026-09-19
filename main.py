import os
from datetime import datetime
from src.config import config
from src.data_fetcher import ETFDataFetcher
from src.analyzer import ETFAnalyzer
from src.notifier import Notifier

def build_dashboard(results: list) -> str:
    now_str = datetime.now().strftime("%Y-%m-%d")
    md = [f"## 📊 Daily ETF 智能决策看板 ({now_str})\n"]
    md.append(f"今日共监测 **{len(results)}** 只核心 ETF\n")
    md.append("| 标的 | 态度 | 评分 | 折溢价状态 | 策略建议 |")
    md.append("| :--- | :--- | :---: | :--- | :--- |")
    
    for r in results:
        md.append(f"| **{r.get('etf_name')}** ({r.get('etf_code')}) | `{r.get('stance')}` | **{r.get('score')}** | {r.get('premium_risk')} | {r.get('strategy_advice')} |")

    md.append("\n### 🎯 标的深度诊断：")
    for r in results:
        md.append(f"\n#### 📌 {r.get('etf_name')} ({r.get('etf_code')})")
        md.append(f"- **宏观背景**: {r.get('macro_and_sector')}")
        md.append(f"- **技术诊断**: {r.get('technical_verdict')}")
        md.append(f"- **风控提示**: ⚠️ {r.get('risk_warning')}")
    
    return "\n".join(md)

def main():
    print(f"🚀 开始执行 ETF 分析: {config.etf_list}")
    fetcher = ETFDataFetcher()
    analyzer = ETFAnalyzer()
    
    results = []
    for code in config.etf_list:
        print(f"-> 正在分析: {code} ...")
        raw_data = fetcher.get_etf_info(code)
        res = analyzer.analyze(raw_data)
        results.append(res)

    dashboard = build_dashboard(results)
    print("\n" + dashboard)
    Notifier.broadcast(dashboard)
    print(">> 推送流程结束。")

if __name__ == "__main__":
    main()
