import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from config import SpeicalRe, parse_money

now = datetime.now()
merged_file_name = f"merged_data_{now.strftime('%m%d')}.json"
# 获取当前脚本所在目录 (__dirname)
current_dir = Path(__file__).resolve().parent
# 构造目标和输出路径
data_json_dir = current_dir.parent / "data_json"
output_path = data_json_dir / merged_file_name


def merge_and_deduplicate_data():
    """
    批量读取 data_json 目录中的所有 json 文件，合并并按 unique_key 去重
    """
    try:
        all_data = merge_all_json()
        print(f"合并前总数据条数: {len(all_data)}")

        # 按 unique_key 去重
        unique_seen = set()
        deduplicated_data = []
        for item in all_data:
            unique_key = item.get("unique_key")
            if not unique_key or unique_key not in unique_seen:
                deduplicated_data.append(item)
                unique_seen.add(unique_key)

        # 字段清洗逻辑
        for item in deduplicated_data:
            # 处理职位名称：相当于 if (!item['职位'] && item['职位名称'])
            if not item.get("职位") and item.get("职位名称"):
                item["职位"] = item["职位名称"]
                del item["职位名称"]
            if not item.get("来源"):
                item["来源"] = "boss"

            # 处理距离：使用正则过滤非数字和小数点的字符
            if item.get("距离"):
                # 兼容处理：确保转换为字符串后再进行正则替换，防止原数据格式为 Number
                item["距离"] = re.sub(r"[^\d.]", "", str(item["距离"]))

        print(f"去重后数据条数: {len(deduplicated_data)}")

        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存到新文件
        # ensure_ascii=False 保证中文字符能够正常写入，indent=2 进行美化输出
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(deduplicated_data, f, ensure_ascii=False, indent=2)

        print(f"合并后的数据已保存到: {output_path}")
        del_files()

    except Exception as e:
        print("处理数据时出错:", e)
        raise e


def merge_all_json() -> list[dict[str, Any]]:
    # 如果目录不存在则提前终止
    if not data_json_dir.exists():
        raise FileNotFoundError(f"目录不存在: {data_json_dir}")

    # 读取 data_json 目录中的所有 .json 文件
    files = os.listdir(data_json_dir)
    json_files = [f for f in files if f.endswith(".json")]

    # 建议：如果是多次运行，最好在读取时排除上次生成的合并文件
    # json_files =[f for f in json_files if f != save_name]

    print(f"找到 {len(json_files)} 个JSON文件")

    # 存储所有数据
    all_data: list[dict[str, Any]] = []

    # 读取每个json文件并合并
    for file_name in json_files:
        file_path = data_json_dir / file_name
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            print(f"读取文件: {file_name}, 数据条数: {len(data)}")
            all_data.extend(data)
        else:
            print(f"读取文件: {file_name}, 警告: 数据不是JSON数组")

    def format_unique_key(ori: str) -> str:
        parts = ori.split("/")
        parts[0] = SpeicalRe.sub('', parts[0])
        parts[1] = SpeicalRe.sub('', parts[1])
        return '/'.join(parts)

    for item in all_data:
        money_float = parse_money(item["薪资"])
        item["薪资"] = f"{money_float['min']}-{money_float['max']}万"
        if money_float["month"]:
            item["薪资"] = item["薪资"] + f".{money_float['month']}月"

        if not item.get('来源'):
            item['来源'] = 'boss'

        companyName: str = item.get("客户公司") or item.get("公司") or ""
        if "•" in companyName:
            companyName = companyName.split("•")[0]
        item["公司"] = SpeicalRe.sub('', companyName)

        # item['unique_key'] = format_unique_key(item['unique_key'])
        # item['unique_item_key'] = format_unique_key(item['unique_item_key'])

    return all_data


# 删除已经合并的json文件
def del_files():
    if not data_json_dir.exists():
        raise FileNotFoundError(f"目录不存在: {data_json_dir}")

    # 读取 data_json 目录中的所有 .json 文件
    files = os.listdir(data_json_dir)
    json_files = [f for f in files if f.endswith(".json") and f != merged_file_name]
    for item in json_files:
        # print(item)
        (data_json_dir / item).unlink(missing_ok=False)
    print("\n文件删除成功")


def get_seen_unique_keys() -> set[str]:
    try:
        json_data = merge_all_json()
        return {item["unique_key"] for item in json_data}
    except:
        return set()


if __name__ == "__main__":
    merge_and_deduplicate_data()
