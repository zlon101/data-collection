# core/poco_helper.py
"""
Poco 实例工厂。

注意：pocoui 1.0.x 的 AirtestInput 驱动不提供 set_touch_timeout()。
控件查找超时通过每次调用时传入 timeout 参数控制（如 wait_for_appearance），
而非在初始化阶段全局设置。
"""

import logging
from poco.drivers.android.uiautomation import AndroidUiautomationPoco

logger = logging.getLogger(__name__)


def create_android_poco(
    use_airtest_input: bool = True,
    screenshot_each_action: bool = False,
    timeout: float = 20.0,  # 保留参数以兼容调用方，当前版本暂不生效
) -> AndroidUiautomationPoco:
    """
    创建 Android Poco 实例。

    Args:
        use_airtest_input: True = 使用 Airtest 的 ADB 触控（更稳定），
                           False = 使用 Poco 自带的触控驱动。
        screenshot_each_action: 每次操作后截图（调试用，会显著降低速度）。
        timeout: 预留参数。各操作的超时请在调用时通过
                 wait_for_appearance(timeout=N) 等方式单独指定。

    Returns:
        已初始化的 AndroidUiautomationPoco 实例。

    Raises:
        RuntimeError: Poco 初始化失败（通常是设备未连接或
                      pocoservice APK 通信异常）。
    """
    try:
        poco = AndroidUiautomationPoco(
            use_airtest_input=use_airtest_input,
            screenshot_each_action=screenshot_each_action,
        )
        logger.info("Poco 初始化成功")
        return poco

    except Exception as exc:
        raise RuntimeError(f"Poco 初始化失败: {exc}") from exc
