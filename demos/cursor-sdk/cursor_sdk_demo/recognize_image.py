"""用 Cursor SDK 提取图片内容，输出为 HTML 文件。

调试：运行前可设置 CURSOR_SDK_LOG=debug（或 info）、CURSOR_SDK_BRIDGE_LOG=1。
超时秒数可用环境变量 CURSOR_SDK_DEMO_TIMEOUT（默认 180）。
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
import threading
from io import BytesIO
from pathlib import Path

from cursor_sdk import (
    Agent,
    CursorAgentError,
    LocalAgentOptions,
    SDKAssistantMessage,
    SDKImage,
    SDKStatusMessage,
    SDKThinkingMessage,
    SDKToolUseMessage,
    SDKUsageMessage,
    TextBlock,
    UserMessage,
)
from dotenv import load_dotenv
from PIL import Image

from common import file_manager
from common.logger import log

DEMO_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
IMAGE_PATH = DEMO_DIR / "b.png"
OUTPUT_PATH = DEMO_DIR / "output.html"
DEFAULT_TIMEOUT_SEC = 180
MAX_IMAGE_SIDE = 1600
JPEG_QUALITY = 85

PROMPT = (
    "图片已作为消息附件提供。请直接根据附件中的全部可见内容提取信息，"
    "并整理为结构清晰的 HTML。"
    "不要使用 read / 打开文件 / 搜索代码库等工具，不要访问磁盘上的图片路径。"
    "只输出完整 HTML 文档（含 <html>、<head>、<body>），"
    "不要编写任何样式（禁止 <style>、style 属性、CSS class 装饰），"
    "用语义化标签与表格表达结构即可。"
    "不要 Markdown、不要代码围栏、不要额外解释。"
)


def _strip_fences(text: str) -> str:
    """去掉模型偶发包裹的 markdown 代码围栏。"""
    stripped = text.strip()
    match = re.fullmatch(r"```(?:html|HTML)?\s*\n?(.*?)\n?```", stripped, re.DOTALL)
    if match:
        return match.group(1).strip()
    return stripped


def _timeout_sec() -> int:
    raw = os.environ.get("CURSOR_SDK_DEMO_TIMEOUT", "").strip()
    if not raw:
        return DEFAULT_TIMEOUT_SEC
    return int(raw)


def _prepare_sdk_image(path: Path) -> SDKImage:
    """压缩并转为 JPEG，降低 SDK 视觉管线压力。"""
    with Image.open(path) as raw:
        image = raw.convert("RGB")
        width, height = image.size
        scale = min(1.0, MAX_IMAGE_SIDE / max(width, height))
        if scale < 1.0:
            image = image.resize(
                (max(1, int(width * scale)), max(1, int(height * scale))),
                Image.Resampling.LANCZOS,
            )
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        data = buffer.getvalue()
        out_size = image.size

    log(
        f"图片压缩: {path.name} {path.stat().st_size}B "
        f"-> jpeg {len(data)}B size={out_size}"
    )
    return SDKImage.from_data(data, "image/jpeg")


def _log_sdk_message(message: object) -> None:
    if isinstance(message, SDKStatusMessage):
        log(f"[status] {message.status}")
        return
    if isinstance(message, SDKThinkingMessage):
        text = (message.text or "").strip()
        if text:
            log(f"[thinking] {text[:120]}")
        return
    if isinstance(message, SDKAssistantMessage):
        parts: list[str] = []
        for block in message.message.content:
            if isinstance(block, TextBlock) and block.text:
                parts.append(block.text)
        chunk = "".join(parts)
        if chunk:
            preview = chunk.replace("\n", "\\n")[:160]
            log(f"[assistant] +{len(chunk)} chars: {preview}")
        return
    if isinstance(message, SDKToolUseMessage):
        log(f"[tool_call] {message.status} name={message.name} call_id={message.call_id}")
        return
    if isinstance(message, SDKUsageMessage):
        usage = message.usage
        log(
            "[usage] "
            f"in={usage.input_tokens} out={usage.output_tokens} "
            f"total={usage.total_tokens}"
        )
        return
    log(f"[event] {type(message).__name__}")


def main() -> None:
    load_dotenv(REPO_ROOT / ".env")
    api_key = os.environ.get("CURSOR_SDK_KEY", "").strip()
    if not api_key:
        log("缺少 CURSOR_SDK_KEY，请在项目根 .env 中配置", level="ERROR")
        sys.exit(1)

    model = os.environ.get("CURSOR_SDK_MODEL", "").strip()
    if not model:
        log("缺少 CURSOR_SDK_MODEL，请在项目根 .env 中配置", level="ERROR")
        sys.exit(1)

    if not IMAGE_PATH.is_file():
        log(f"图片不存在: {IMAGE_PATH}", level="ERROR")
        sys.exit(1)

    timeout_sec = _timeout_sec()
    sdk_image = _prepare_sdk_image(IMAGE_PATH)
    # 使用仓库外临时目录，减少 Local Agent 注入的项目 rules/tools 上下文
    work_cwd = Path(tempfile.mkdtemp(prefix="cursor-sdk-vision-"))

    log(f"图片: {IMAGE_PATH}")
    log(f"输出: {OUTPUT_PATH}")
    log(f"模型: {model} (CURSOR_SDK_MODEL)")
    log(f"cwd: {work_cwd}")
    log(f"超时: {timeout_sec}s (CURSOR_SDK_DEMO_TIMEOUT)")
    log(f"CURSOR_SDK_LOG={os.environ.get('CURSOR_SDK_LOG') or '(unset)'}")
    log(f"CURSOR_SDK_BRIDGE_LOG={os.environ.get('CURSOR_SDK_BRIDGE_LOG') or '(unset)'}")

    timed_out = False

    try:
        with Agent.create(
            model=model,
            api_key=api_key,
            local=LocalAgentOptions(cwd=str(work_cwd)),
        ) as agent:
            run = agent.send(
                UserMessage(
                    text=PROMPT,
                    images=[sdk_image],
                )
            )
            log(f"agent_id={agent.agent_id}")
            log(f"run_id={run.id}")

            def _on_timeout() -> None:
                nonlocal timed_out
                timed_out = True
                log(f"已达超时 {timeout_sec}s，尝试 cancel", level="WARNING")
                if run.supports("cancel"):
                    run.cancel()
                else:
                    reason = run.unsupported_reason("cancel")
                    log(f"cancel 不可用: {reason}", level="ERROR")

            timer = threading.Timer(timeout_sec, _on_timeout)
            timer.daemon = True
            timer.start()
            try:
                stop_status = run.on_did_change_status(
                    lambda status: log(f"[status-change] {status}")
                )
                try:
                    for message in run.messages():
                        _log_sdk_message(message)
                finally:
                    stop_status()
                result = run.wait()
            finally:
                timer.cancel()
    except CursorAgentError as err:
        log(
            f"启动失败: {err.message}, retryable={err.is_retryable}",
            level="ERROR",
        )
        sys.exit(1)

    log(f"终态 status={result.status} run_id={result.id}")
    if timed_out or result.status == "cancelled":
        log("因超时或取消结束，未写入 HTML", level="ERROR")
        sys.exit(3)
    if result.status == "error":
        log(f"run 失败: {result.id}", level="ERROR")
        sys.exit(2)

    html = _strip_fences(result.result or "")
    if not html:
        log("识别结果为空", level="ERROR")
        sys.exit(2)

    file_manager.write_text(html, OUTPUT_PATH)
    log(f"已写入 HTML: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
