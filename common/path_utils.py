# common/path_utils.py
"""项目根目录定位工具。"""

from pathlib import Path


def get_project_root() -> Path:
    """返回当前工作目录，约定所有命令必须从项目根执行。"""
    return Path.cwd()
