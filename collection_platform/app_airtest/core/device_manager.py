# Android 设备连接（USB / WiFi）

import os
import logging
from typing import Literal
from airtest.core.api import connect_device, auto_setup
from airtest.core.helper import set_logdir

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def setup_android_device(
    adb_path: str,  # M1 Homebrew 路径
    mode: Literal["usb", "wifi"] = "usb",
    wifi_host: str = "",
    wifi_port: int = 5555,
    device_serial: str = "",
) -> None:
    """
    初始化 Android 设备连接。

    Args:
        mode: 连接模式，"usb" 或 "wifi"。
        wifi_host: WiFi 模式下设备的 IP 地址。
        wifi_port: WiFi 模式下 ADB 端口，默认 5555。
        device_serial: 指定设备序列号（多设备时必填）。
        adb_path: ADB 可执行文件路径（M1 推荐显式指定）。

    Raises:
        ValueError: 参数校验失败。
        ConnectionError: 设备连接失败。
    """
    # --- 显式指定 ADB 路径，规避 M1 内置二进制问题 ---
    if adb_path and os.path.isfile(adb_path):
        # Airtest 通过环境变量读取自定义 ADB 路径
        os.environ["AIRTEST_ADB_PATH"] = adb_path
        logger.info("使用自定义 ADB 路径: %s", adb_path)
    else:
        logger.warning("未找到指定 ADB 路径 %s，将使用 Airtest 内置 ADB", adb_path)

    # --- 构造连接 URI ---
    # 格式: Android://host:port/serial?参数
    if mode == "usb":
        # USB 连接：serial 可为空（自动选择第一台），多设备时须指定
        uri = f"Android:///{device_serial}"
        logger.info("尝试 USB 连接，serial=%s", device_serial or "(自动)")

    elif mode == "wifi":
        if not wifi_host:
            raise ValueError("WiFi 模式需要提供 wifi_host (设备 IP)")
        # WiFi 连接前须先在设备上执行: adb tcpip 5555
        uri = f"Android://{wifi_host}:{wifi_port}/{device_serial}"
        logger.info("尝试 WiFi 连接，目标: %s:%d", wifi_host, wifi_port)

    else:
        raise ValueError(f"不支持的连接模式: {mode}，请使用 'usb' 或 'wifi'")

    # --- 执行连接 ---
    try:
        dev = connect_device(uri)
        logger.info("设备连接成功: %s", dev)
    except Exception as exc:
        raise ConnectionError(f"设备连接失败，URI={uri}，原因: {exc}") from exc


def setup_with_auto(script_path: str = __file__) -> None:
    """
    使用 auto_setup 进行一键初始化（适合脚本顶部快速接入）。
    auto_setup 会自动处理日志目录、截图目录等。

    Args:
        script_path: 当前脚本的 __file__ 路径，用于确定日志存储位置。
    """
    # auto_setup 第一个参数是日志根目录，第二个是设备列表
    auto_setup(
        basedir=os.path.dirname(script_path),
        devices=["Android:///"],          # 自动连接第一台 USB 设备
        logdir=os.path.join(
            os.path.dirname(script_path), "outputs", "logs"
        ),
    )
    logger.info("auto_setup 初始化完成")