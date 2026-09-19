import requests
from src.config import config

class Notifier:
    @staticmethod
    def send_wechat(content: str):
        if not config.wechat_webhook:
            return
        requests.post(config.wechat_webhook, json={"msgtype": "markdown", "markdown": {"content": content}})

    @staticmethod
    def send_feishu(content: str):
        if not config.feishu_webhook:
            return
        requests.post(config.feishu_webhook, json={"msg_type": "text", "content": {"text": content}})

    @staticmethod
    def send_dingtalk(content: str):
        if not config.dingtalk_webhook:
            return
        requests.post(config.dingtalk_webhook, json={"msgtype": "markdown", "markdown": {"title": "ETF每日决策看板", "text": content}})

    @classmethod
    def broadcast(cls, report_markdown: str):
        cls.send_wechat(report_markdown)
        cls.send_feishu(report_markdown)
        cls.send_dingtalk(report_markdown)
