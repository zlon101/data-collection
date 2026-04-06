# config/devices.py
"""
设备连接配置中心。
所有与硬件环境相关的常量都在此统一管理，脚本中直接 import 使用，
避免在业务代码里散落硬编码路径/IP/包名。
"""

# ── ADB 路径 ───────────────────────────────────────────────────────────────
# macOS M1 通过 Homebrew 安装的原生 ARM64 ADB 路径。
# 若使用其他路径，修改此处即可全局生效。
ADB_PATH: str = "/opt/homebrew/bin/adb"

# ── 设备连接参数 ────────────────────────────────────────────────────────────
# USB 模式：serial 留空表示自动选择第一台已连接设备；
# 多设备并联时填写 `adb devices` 输出的序列号，例如 "emulator-5554"。
USB_DEVICE_SERIAL: str = ""

# WiFi 模式：使用前须先在设备上执行 `adb tcpip 5555`，
# 然后将设备 IP 填入 WIFI_HOST。
WIFI_HOST: str = ""
WIFI_PORT: int = 5555

# ── 目标 App 信息 ──────────────────────────────────────────────────────────
# 替换为实际测试 App 的包名与入口 Activity。
# 获取方式：adb shell dumpsys window | grep mCurrentFocus
APP_PACKAGE: str = "com.example.app"
APP_ACTIVITY: str = "com.example.app.MainActivity"

# ── Poco 超时配置（秒） ────────────────────────────────────────────────────
# 控件查找的全局等待超时，生产环境可适当调低以尽早暴露问题。
POCO_DEFAULT_TIMEOUT: float = 20.0

# App 冷启动后等待 UI 就绪的时间，根据设备性能调整。
APP_COLD_START_WAIT: float = 3.0
