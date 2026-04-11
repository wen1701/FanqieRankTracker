"""
一次性迁移脚本：将现有的 Markdown 榜单文件转换为 JSON 快照格式。
运行一次后即可废弃。
"""
import os
import re
import json
import glob


def parse_md_to_json(md_path: str) -> dict:
    """解析一个 Markdown 榜单文件，返回结构化 JSON 数据。"""
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 提取日期
    date_match = re.search(r"\*\*采集日期\*\*:\s*(\d{4}-\d{2}-\d{2})", content)
    date_str = date_match.group(1) if date_match else ""

    result = {"date": date_str, "categories": []}

    categories_raw = content.split("\n## ")

    for cat_raw in categories_raw[1:]:
        lines = cat_raw.strip().split("\n")
        cat_name = lines[0].strip()

        books = []
        book_blocks = cat_raw.split("\n### ")

        for block in book_blocks[1:]:
            book_info = {
                "title": "未知",
                "url": "#",
                "cover": "",
                "author": "未知",
                "reads": "未知",
                "intro": "无",
            }

            # 标题和链接
            title_match = re.search(
                r"^\d+\.\s*\[(.*?)\]\((.*?)\)", block, re.MULTILINE
            )
            if title_match:
                book_info["title"] = title_match.group(1).strip()
                book_info["url"] = title_match.group(2).strip()

            # 封面
            cover_match = re.search(r"!\[.*?\]\((.*?)\)", block)
            if cover_match:
                book_info["cover"] = cover_match.group(1).strip()

            # 作者
            author_match = re.search(r"-\s*\*\*作者\*\*:\s*(.*)", block)
            if author_match:
                book_info["author"] = author_match.group(1).strip()

            # 在读
            reads_match = re.search(r"-\s*\*\*在读\*\*:\s*(.*)", block)
            if reads_match:
                book_info["reads"] = reads_match.group(1).strip()

            # 简介
            intro_match = re.search(r"-\s*\*\*简介\*\*:\s*(.*)", block)
            if intro_match:
                book_info["intro"] = intro_match.group(1).strip()

            books.append(book_info)

        result["categories"].append({"name": cat_name, "books": books})

    return result


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    md_files = sorted(glob.glob(os.path.join(data_dir, "fanqie_female_new_ranks_*.md")))

    if not md_files:
        print("未找到任何 Markdown 文件。")
        return

    for md_path in md_files:
        basename = os.path.basename(md_path)
        json_name = basename.replace(".md", ".json")
        json_path = os.path.join(data_dir, json_name)

        if os.path.exists(json_path):
            print(f"跳过已存在: {json_name}")
            continue

        print(f"迁移: {basename} -> {json_name}")
        data = parse_md_to_json(md_path)
        print(f"  分类数: {len(data['categories'])}")
        for cat in data["categories"]:
            print(f"    {cat['name']}: {len(cat['books'])} 本")

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print("\n✅ 迁移完成！")


if __name__ == "__main__":
    main()
