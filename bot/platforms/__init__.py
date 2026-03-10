# -*- coding: utf-8 -*-
"""
===================================
平台适配器模块
===================================

包含各平台的 Webhook 处理和消息解析逻辑。

支持 Webhook 模式：需要公网 IP，配置回调 URL
"""

from bot.platforms.base import BotPlatform

# 所有可用平台（Webhook 模式）
ALL_PLATFORMS = {
}

__all__ = [
    'BotPlatform',
    'ALL_PLATFORMS',
]
