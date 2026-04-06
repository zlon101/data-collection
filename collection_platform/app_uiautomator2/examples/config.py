#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from typing import TypedDict


BlackCompany = ["UMU", "外企德科", "兴业数金", "东软"]

JobKeys = ["web", "Web", "WEB", "前端", "全栈", "可视化"]
# 非中文非字母
SpeicalRe = re.compile(r"[^a-zA-Z\u4e00-\u9fa5]+")

MoneyMin = 1.4
MAX_DISTANCE = 30


# 1. 定义字典的结构
class Statistics(TypedDict):
    min: float
    max: float
    month: int | None


def parse_money(moneyStr: str = "") -> Statistics:
    def _parse(s: str) -> float:
        a = float(s)
        if not a:
            return 0.0
        if a < 30:
            # 年终（多少个月）
            return a
        return a if a < 1000 else a / 10000

    nums = [_parse(n) for n in re.findall(r"\d+\.?\d*", moneyStr)]
    count = len(nums)
    min_val = nums[0] if count else 99
    return {
        "min": min_val,
        "max": nums[1] if len(nums) > 1 else min_val,
        "month": int(nums[2]) if len(nums) > 2 else None,
    }


print(parse_money("8000-120000元.15月"))
