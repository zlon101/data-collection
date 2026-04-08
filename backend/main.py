# backend/main.py
"""
FastAPI 后端入口。

启动方式（在项目根目录下）：
    uv run uvicorn backend.main:app --reload --port 8000
"""

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router

app = FastAPI(
    title="数据采集分析平台",
    description="微信公众号 / App / 网页数据采集与 AI 分析",
    version="1.0.0",
)

# 允许前端开发服务器跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "数据采集分析平台 API", "docs": "/docs"}
