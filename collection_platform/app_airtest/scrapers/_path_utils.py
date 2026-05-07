# scrapers/_path_utils.py
"""项目根目录定位工具（app_airtest 独立模块，不依赖 workspace）。"""

from pathlib import Path


def get_project_root() -> Path:
    """从当前工作目录向上搜索，找到包含 pyproject.toml + collection_platform/ 的目录，返回项目根。"""
    for parent in Path.cwd().parents:
        if (parent / "pyproject.toml").exists() and (parent / "collection_platform").is_dir():
            return parent
    raise RuntimeError("未找到项目根目录")
