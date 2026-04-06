#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常类定义
"""


class MultipleElementsError(Exception):
    """
    字段匹配到多个元素
    
    触发条件:
    - 单个 resourceId 匹配到多个元素
    - 且未配置 textPattern
    - 或配置了 textPattern 但过滤后仍有多个元素
    
    解决方法:
    - 添加或优化 textPattern 正则表达式
    """
    pass


class ParseTimeoutError(Exception):
    """
    达到最大滚动次数但未检测到底部标识
    
    触发条件:
    - scroll_count >= max_scroll_times
    - 且未检测到底部标识元素
    
    可能原因:
    - bottom_indicator_resourceId 配置错误
    - 页面确实没有底部标识
    - 页面非常长（需要增大 max_scroll_times）
    
    错误信息包含:
    - 已滚动次数
    - 未找到的字段列表
    - 底部标识配置
    """
    pass


class BottomReachedError(Exception):
    """
    检测到底部标识，但必填字段未找全
    
    触发条件:
    - 检测到 bottom_indicator_resourceId 元素存在
    - 但仍有 optional=False 的字段未找到
    
    可能原因:
    - 字段 resourceId 配置错误
    - 字段 textPattern 配置错误
    - 页面确实没有该字段内容
    
    错误信息包含:
    - 未找到的必填字段列表及其配置
    - 已找到的字段列表
    """
    pass


class ScrollFailedError(Exception):
    """
    滚动操作失败
    
    触发条件:
    - device.swipe() 执行时抛出异常
    
    可能原因:
    - adb 连接断开
    - 设备无响应
    - 页面卡死
    """
    pass
