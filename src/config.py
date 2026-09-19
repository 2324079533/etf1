import os
from dataclasses import dataclass, field
from typing import List

@dataclass
class Config:
    # 默认监控标的池：沪深300(510300)、创业板(159915)、芯片(512760)、纳指ETF(513100)、黄金ETF(518880)
    etf_list: List[str] = field(default_factory=lambda: [
        s.strip() for s in os.getenv("ETF_LIST", "510300,159915,512760,513100,518880").split(",") if s.strip()
    ])
    
    # LLM 配置
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
    llm_model: str = os.getenv("LLM_MODEL", "deepseek-chat")
    
    # Webhook 配置
    wechat_webhook: str = os.getenv("WECHAT_WEBHOOK", "")
    feishu_webhook: str = os.getenv("FEISHU_WEBHOOK", "")
    dingtalk_webhook: str = os.getenv("DINGTALK_WEBHOOK", "")

config = Config()
