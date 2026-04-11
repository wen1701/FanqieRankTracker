"""
构建 latest_ranks.json：
1. 加载最近两天的 JSON 快照
2. 按分类对比趋势（新上榜/掉榜/排名变化/阅读量变化）
3. 可选调用 Gemini Flash 生成 AI 总结
4. 输出 latest_ranks.json + trends/YYYY-MM-DD.json
"""
import os
import re
import json
import glob
import sys


def parse_reads(reads_str: str) -> float:
    """将 '15.2万' 这样的字符串转为数值，用于比较。"""
    if not reads_str or reads_str == "未知":
        return 0
    s = reads_str.strip().replace(",", "")
    try:
        if "万" in s:
            return float(s.replace("万", "")) * 10000
        return float(s)
    except ValueError:
        return 0


def format_reads_change(diff: float) -> str:
    """格式化阅读量变化。"""
    if abs(diff) >= 10000:
        return f"{'+' if diff > 0 else ''}{diff / 10000:.1f}万"
    return f"{'+' if diff > 0 else ''}{int(diff)}"


def load_snapshot(path: str) -> dict:
    """加载一个 JSON 快照文件。"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compare_categories(today_cats: list, prev_cats: list) -> dict:
    """
    对比两天的分类数据，返回每个分类的趋势信息。
    key = 分类名, value = trend dict
    """
    # 构建 prev 的索引: cat_name -> {url: (rank, reads_str, title)}
    prev_index = {}
    for cat in prev_cats:
        url_map = {}
        for i, book in enumerate(cat.get("books", [])):
            url_map[book["url"]] = {
                "rank": i + 1,
                "reads": book.get("reads", "未知"),
                "title": book.get("title", "未知"),
            }
        prev_index[cat["name"]] = url_map

    trends = {}
    for cat in today_cats:
        cat_name = cat["name"]
        prev_urls = prev_index.get(cat_name, {})
        today_books = cat.get("books", [])

        new_books = []
        dropped_books = []
        risers = []
        fallers = []
        reads_growth = []

        today_urls = set()
        for i, book in enumerate(today_books):
            url = book["url"]
            today_urls.add(url)
            today_rank = i + 1
            title = book.get("title", "未知")

            if url in prev_urls:
                prev_info = prev_urls[url]
                prev_rank = prev_info["rank"]
                rank_change = prev_rank - today_rank  # 正数=上升

                if rank_change > 0:
                    risers.append({"title": title, "change": f"+{rank_change}"})
                elif rank_change < 0:
                    fallers.append({"title": title, "change": str(rank_change)})

                # 阅读量变化
                today_reads = parse_reads(book.get("reads", ""))
                prev_reads = parse_reads(prev_info["reads"])
                if today_reads > 0 and prev_reads > 0:
                    diff = today_reads - prev_reads
                    if diff != 0:
                        reads_growth.append(
                            {"title": title, "growth": format_reads_change(diff)}
                        )
            else:
                new_books.append(title)

        # 掉出榜单的书
        for url, info in prev_urls.items():
            if url not in today_urls:
                dropped_books.append(info["title"])

        # 排序：涨幅最大的在前
        risers.sort(key=lambda x: int(x["change"].replace("+", "")), reverse=True)
        fallers.sort(key=lambda x: int(x["change"]))
        reads_growth.sort(
            key=lambda x: parse_reads(x["growth"].replace("+", "")), reverse=True
        )

        trends[cat_name] = {
            "new_count": len(new_books),
            "dropped_count": len(dropped_books),
            "new_books": new_books[:5],
            "dropped_books": dropped_books[:5],
            "top_risers": risers[:3],
            "top_fallers": fallers[:3],
            "reads_growth": reads_growth[:3],
            "summary": "",  # AI 总结，由 generate_ai_summaries 填充
        }

    return trends


def generate_trend_summary_text(cat_name: str, trend: dict) -> str:
    """生成基于规则的简短趋势文本（作为 AI 总结不可用时的 fallback）。"""
    parts = []
    if trend["new_count"] > 0:
        parts.append(f"新增{trend['new_count']}本上榜")
    if trend["dropped_count"] > 0:
        parts.append(f"{trend['dropped_count']}本掉出")
    if trend["top_risers"]:
        r = trend["top_risers"][0]
        parts.append(f"《{r['title']}》排名上升{r['change']}位")
    if trend["reads_growth"]:
        g = trend["reads_growth"][0]
        parts.append(f"《{g['title']}》阅读量{g['growth']}")
    if not parts:
        parts.append("榜单无明显变动")
    return "；".join(parts) + "。"


def build_ai_prompt(cat_name: str, cat: dict, trend_ctx: str) -> str:
    """构建 AI 总结的 prompt。"""
    intros = []
    for i, book in enumerate(cat.get("books", [])[:20]):
        intros.append(
            f"{i+1}. 《{book['title']}》- {book.get('author', '未知')}\n"
            f"   在读：{book.get('reads', '未知')}\n"
            f"   简介：{book.get('intro', '无')[:200]}"
        )
    intros_text = "\n".join(intros)

    return f"""你是一位网文行业分析师。以下是番茄小说「{cat_name}」分类新书榜 Top 20 的书籍信息。

{intros_text}

榜单动态：{trend_ctx}

请用 2-3 段简短的话总结：
1. 这个分类当前的热门题材和趋势（哪些元素、设定出现频率高）
2. 读者偏好风向（甜宠/虐/爽/日常等方向）
3. 有没有值得关注的差异化新作

要求：简洁有力，像专业书评人的快评。不要逐本分析，聚焦整体趋势。总字数控制在200字以内。"""


def generate_ai_summaries(categories: list, trends: dict,
                          api_key: str, base_url: str,
                          model: str) -> dict:
    """通过 OpenAI 兼容 API 为每个分类生成 AI 总结。

    环境变量：
        API_BASE_URL - API 基础地址（如 https://api.zscc.in/v1）
        API_KEY      - API 密钥
        API_MODEL    - 模型名称（如 kimi-k2.5-cc）
    """
    try:
        from openai import OpenAI
    except ImportError:
        print("⚠️  openai 库未安装，跳过 AI 总结。pip install openai")
        return trends

    client = OpenAI(api_key=api_key, base_url=base_url)

    for cat in categories:
        cat_name = cat["name"]
        if cat_name not in trends:
            continue

        trend = trends[cat_name]
        trend_ctx = generate_trend_summary_text(cat_name, trend)
        prompt = build_ai_prompt(cat_name, cat, trend_ctx)

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7,
            )
            trends[cat_name]["summary"] = response.choices[0].message.content.strip()
            print(f"  ✅ AI 总结: {cat_name}")
        except Exception as e:
            print(f"  ❌ AI 总结失败 {cat_name}: {e}")
            trends[cat_name]["summary"] = generate_trend_summary_text(
                cat_name, trend
            )

    return trends


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    trends_dir = os.path.join(data_dir, "trends")
    os.makedirs(trends_dir, exist_ok=True)

    # 查找 JSON 快照文件
    snapshots = sorted(
        glob.glob(os.path.join(data_dir, "fanqie_female_new_ranks_*.json"))
    )

    if not snapshots:
        print("未找到任何 JSON 快照文件。请先运行迁移脚本或爬虫。")
        sys.exit(1)

    # 加载最新的快照
    latest_path = snapshots[-1]
    latest_data = load_snapshot(latest_path)
    print(f"最新快照: {os.path.basename(latest_path)} ({latest_data['date']})")

    # 加载前一天的快照（如果有）
    prev_data = None
    prev_date = ""
    if len(snapshots) >= 2:
        prev_path = snapshots[-2]
        prev_data = load_snapshot(prev_path)
        prev_date = prev_data.get("date", "")
        print(f"对比快照: {os.path.basename(prev_path)} ({prev_date})")

    # 对比趋势
    if prev_data:
        trends = compare_categories(
            latest_data["categories"], prev_data["categories"]
        )
    else:
        print("仅有一天数据，无法生成趋势对比。")
        trends = {
            cat["name"]: {
                "new_count": 0,
                "dropped_count": 0,
                "new_books": [],
                "dropped_books": [],
                "top_risers": [],
                "top_fallers": [],
                "reads_growth": [],
                "summary": "首日数据，暂无趋势对比。",
            }
            for cat in latest_data["categories"]
        }

    # ========== AI 总结：通过 API_BASE_URL / API_KEY / API_MODEL 配置 ==========
    api_base_url = os.environ.get("API_BASE_URL", "")
    api_key = os.environ.get("API_KEY", "")
    api_model = os.environ.get("API_MODEL", "")

    if api_base_url and api_key and api_model:
        print(f"\n正在使用 {api_model} 生成 AI 总结...")
        print(f"  API: {api_base_url}")
        trends = generate_ai_summaries(
            latest_data["categories"], trends,
            api_key, api_base_url, api_model
        )
    else:
        missing = [k for k, v in {"API_BASE_URL": api_base_url, "API_KEY": api_key, "API_MODEL": api_model}.items() if not v]
        print(f"\n未配置 AI 服务（缺少: {', '.join(missing)}），使用规则摘要替代。")
        for cat_name, trend in trends.items():
            if not trend.get("summary"):
                trend["summary"] = generate_trend_summary_text(cat_name, trend)

    # 组装输出
    output = {
        "date": latest_data["date"],
        "prev_date": prev_date,
        "categories": [],
    }

    for cat in latest_data["categories"]:
        cat_name = cat["name"]
        cat_output = {
            "name": cat_name,
            "trend": trends.get(cat_name, {}),
            "books": cat.get("books", []),
        }
        output["categories"].append(cat_output)

    # 写入 latest_ranks.json
    out_path = os.path.join(data_dir, "latest_ranks.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 已生成: {out_path}")

    # 写入 trends/YYYY-MM-DD.json
    trend_path = os.path.join(trends_dir, f"{latest_data['date']}.json")
    trend_output = {
        "date": latest_data["date"],
        "prev_date": prev_date,
        "trends": trends,
    }
    with open(trend_path, "w", encoding="utf-8") as f:
        json.dump(trend_output, f, ensure_ascii=False, indent=2)
    print(f"✅ 趋势存档: {trend_path}")


if __name__ == "__main__":
    main()
