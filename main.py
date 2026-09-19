import os
import json
import requests
import datetime
import akshare as ak
import pandas as pd
from openai import OpenAI

# ================= 1. 读取环境变量 =================
ETF_LIST_STR = os.getenv("ETF_LIST", "510300,510500")
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

WECHAT_WEBHOOK = os.getenv("WECHAT_WEBHOOK")
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK")
DINGTALK_WEBHOOK = os.getenv("DINGTALK_WEBHOOK")

# ================= 2. 增强型数据获取 (含技术指标与排错) =================
def get_market_benchmark():
    """获取上证指数作为大盘情绪基准"""
    try:
        df = ak.stock_zh_index_daily(symbol="sh000001")
        if df is None or df.empty:
            print("⚠️ 警告: 未能获取到上证指数基准数据，可能是由于 GitHub 海外 IP 被限制。")
            return None
        recent = df.tail(3)[['date', 'open', 'close', 'volume']]
        recent['date'] = recent['date'].astype(str)
        return recent.to_dict('records')
    except Exception as e:
        print(f"❌ 获取大盘基准发生异常: {e}")
        return None

def get_enhanced_etf_data(etf_code):
    """获取特定 ETF 数据并计算移动均线等技术指标"""
    try:
        # 清理代码前后的空格，防止配置错误
        etf_code = etf_code.strip()
        df = ak.fund_etf_hist_em(symbol=etf_code, period="daily", adjust="qfq")
        
        # --- 诊断日志逻辑 ---
        if df is None or df.empty:
            print(f"⚠️ 警告: 接口未返回 {etf_code} 的数据。请检查：1. 代码是否为纯数字 2. GitHub海外IP是否被临时拦截。")
            return None
        if len(df) < 20:
            print(f"⚠️ 警告: {etf_code} 交易天数仅 {len(df)} 天，不足20天无法计算完整均线，跳过该 ETF。")
            return None
        
        # --- 计算技术指标 ---
        df['MA5'] = df['收盘'].rolling(window=5).mean().round(3)
        df['MA10'] = df['收盘'].rolling(window=10).mean().round(3)
        df['MA20'] = df['收盘'].rolling(window=20).mean().round(3)
        df['涨跌幅(%)'] = df['收盘'].pct_change().apply(lambda x: round(x * 100, 2))
        
        # 提取最近 3 天的深度数据
        recent_data = df.tail(3)[['日期', '收盘', '涨跌幅(%)', '成交量', 'MA5', 'MA10', 'MA20']]
        recent_data['日期'] = recent_data['日期'].astype(str)
        
        # 判断多空趋势 (以 20 日线为短线牛熊分界)
        last_close = df.iloc[-1]['收盘']
        last_ma20 = df.iloc[-1]['MA20']
        trend = "多头排列 📈" if last_close > last_ma20 else "空头排列 📉"
        
        return {
            "趋势状态": trend,
            "近期量价": recent_data.to_dict('records')
        }
    except Exception as e:
        print(f"❌ 获取 ETF {etf_code} 数据发生异常: {e}")
        return None

# ================= 3. 大模型深度解析 =================
def generate_professional_report(market_data, etf_data_dict):
    if not LLM_API_KEY:
        return "⚠️ 未配置 LLM_API_KEY，无法生成分析报告，请在 Secrets 中配置。"
    
    client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    
    market_info = json.dumps(market_data, ensure_ascii=False) if market_data else "未能获取到大盘数据，请仅分析个别 ETF。"
    
    prompt = f"""
    你是一位顶级的华尔街量化策略分析师。请根据提供的A股大盘基准数据和特定 ETF 数据，撰写一份结构化、排版精美、富有洞察力的每日投研报告。

    【输入数据】
    1. 大盘基准(上证指数)近3日数据: {market_info}
    2. 个别 ETF 技术面与量价数据: {json.dumps(etf_data_dict, ensure_ascii=False)}

    【输出格式要求】（必须严格遵守以下 Markdown 结构和 Emoji 风格）
    
    ## 🌐 每日市场整体状况分析
    (用一小段精炼的语言总结今天大盘的整体情绪、资金面表现以及宏观趋势)

    ---
    ## 📊 单只 ETF 深度解析
    (为每一个输入的 ETF 生成以下结构)
    
    ### 📌 [填入 ETF 代码及名称猜测]
    * **核心技术面**：结合 MA5/MA10/MA20 均线系统分析支撑与阻力。
    * **量价配合**：分析近3日成交量与涨跌幅的配合情况（如缩量下跌、放量突破等）。
    * **趋势定性**：说明目前处于左侧交易还是右侧交易区间。
    * **💡 策略建议**：给出明确的【买入/持有/观望/减仓】建议及止损止盈参考位。

    要求：
    1. 语言要专业、客观，数据驱动，切忌废话。
    2. 多使用加粗 **文本** 来突出关键点位和核心结论。
    3. 整体字数控制在 800 字左右，排版必须极度清爽适合手机端阅读。
    """
    
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "你是一个严谨、数据驱动的量化基金经理。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4 # 降低温度，减少幻觉，提高严谨性
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ 大模型请求失败，请检查 API Key 或网络连通性: {e}"

# ================= 4. Webhook 分发 =================
def push_markdown_msg(msg):
    title = f"📈 量化 ETF 投研日报 ({datetime.datetime.now().strftime('%m-%d')})"
    
    if WECHAT_WEBHOOK:
        try:
            requests.post(WECHAT_WEBHOOK, json={"msgtype": "markdown", "markdown": {"content": f"# {title}\n{msg}"}})
            print("✅ 成功推送到企业微信")
        except Exception as e:
            print(f"企微推送失败: {e}")
            
    if DINGTALK_WEBHOOK:
        try:
            requests.post(DINGTALK_WEBHOOK, json={"msgtype": "markdown", "markdown": {"title": title, "text": f"# {title}\n{msg}"}})
            print("✅ 成功推送到钉钉")
        except Exception as e:
            print(f"钉钉推送失败: {e}")
            
    if FEISHU_WEBHOOK:
        try:
            requests.post(FEISHU_WEBHOOK, json={"msg_type": "text", "content": {"text": f"{title}\n\n{msg}"}})
            print("✅ 成功推送到飞书")
        except Exception as e:
            print(f"飞书推送失败: {e}")

# ================= 5. 主执行逻辑 =================
def main():
    print("🔄 开始执行自动化 ETF 投研工作流...")
    
    print("📊 正在获取大盘基准数据(上证指数)...")
    market_data = get_market_benchmark()
    
    # 解析逗号分隔的 ETF 列表
    etf_list = [e.strip() for e in ETF_LIST_STR.split(",") if e.strip()]
    if not etf_list:
        print("❌ 未在环境变量中发现有效的 ETF_LIST 配置，请检查 Secrets。")
        return

    etf_data_dict = {}
    
    for etf in etf_list:
        print(f"🔍 正在深度分析 ETF: {etf} 并计算均线指标...")
        data = get_enhanced_etf_data(etf)
        if data:
            etf_data_dict[etf] = data
            
    if not etf_data_dict:
        print("❌ 所有配置的 ETF 数据获取全部失败，退出程序。请在上方日志查看具体警告信息。")
        return

    print("🧠 正在利用大模型生成结构化投研报告...")
    report = generate_professional_report(market_data, etf_data_dict)
    
    print("🚀 正在推送报告至通讯软件...")
    push_markdown_msg(report)
    print("🎉 任务圆满完成！")

if __name__ == "__main__":
    main()
