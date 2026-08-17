#!/usr/bin/env python3
"""Validate and append one day's sales-growth content to data.json."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

CATEGORIES = ["销售认知", "实战技巧", "客户经营", "执行心态", "团队管理"]
AUDIENCES = {"老板", "店长", "销售", "全员", "老板/店长", "店长/销售"}
ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data.json"
BANK_PATH = ROOT / "content_bank.json"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_items(raw, date: str):
    items = raw.get("items", raw) if isinstance(raw, dict) else raw
    if not isinstance(items, list) or len(items) < 5:
        raise ValueError("每天至少需要5条内容")
    seen_categories, seen_titles, clean = set(), set(), []
    for idx, item in enumerate(items, 1):
        if not isinstance(item, dict):
            raise ValueError(f"第{idx}条不是对象")
        missing = {"category", "audience", "title", "content", "action"} - set(item)
        if missing:
            raise ValueError(f"第{idx}条缺少字段: {sorted(missing)}")
        category = str(item["category"]).strip()
        audience = str(item["audience"]).strip()
        title = str(item["title"]).strip()
        content = re.sub(r"\s+", " ", str(item["content"]).strip())
        action = re.sub(r"\s+", " ", str(item["action"]).strip())
        if category not in CATEGORIES:
            raise ValueError(f"第{idx}条分类不正确: {category}")
        if audience not in AUDIENCES:
            raise ValueError(f"第{idx}条对象不正确: {audience}")
        if not 6 <= len(title) <= 24:
            raise ValueError(f"第{idx}条标题长度应为6-24字")
        if not 45 <= len(content) <= 180:
            raise ValueError(f"第{idx}条正文长度应为45-180字")
        if not 12 <= len(action) <= 60:
            raise ValueError(f"第{idx}条行动长度应为12-60字")
        if title in seen_titles:
            raise ValueError(f"标题重复: {title}")
        seen_titles.add(title)
        seen_categories.add(category)
        clean.append({
            "id": f"{date.replace('-', '')}-{idx:02d}", "category": category,
            "audience": audience, "title": title, "content": content, "action": action,
        })
    missing_categories = set(CATEGORIES) - seen_categories
    if missing_categories:
        raise ValueError(f"每天必须覆盖5个分类，缺少: {sorted(missing_categories)}")
    return clean


def similarity_tokens(text: str):
    return {text[i:i+4] for i in range(max(0, len(text)-3))}


def reject_near_duplicates(new_items, db):
    old = [x for day in db.get("data", {}).values() for x in day]
    for new in new_items:
        a = similarity_tokens(new["title"] + new["content"])
        for prev in old:
            b = similarity_tokens(prev.get("title", "") + prev.get("content", ""))
            if a and b and len(a & b) / max(1, min(len(a), len(b))) > 0.72:
                raise ValueError(f"内容与历史记录过于相似: {new['title']} / {prev.get('title')}")


def items_from_bank(date: str, db):
    bank = load_json(BANK_PATH)
    used_titles = {x.get("title") for day in db.get("data", {}).values() for x in day}
    groups = {}
    for item in bank:
        groups.setdefault(int(item["bank_day"]), []).append(item)
    for day in sorted(groups):
        group = groups[day]
        if all(x.get("title") not in used_titles for x in group):
            return normalize_items(group, date)
    raise ValueError("备用内容库已经用完，需要补充新内容")


def validate_database(db):
    if db.get("timezone") != "Asia/Shanghai":
        raise ValueError("timezone必须是Asia/Shanghai")
    if int(db.get("daily_minimum", 0)) < 5:
        raise ValueError("daily_minimum不能小于5")
    for date, items in db.get("data", {}).items():
        datetime.strptime(date, "%Y-%m-%d")
        normalize_items(items, date)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, help="包含当日5条内容的JSON文件")
    parser.add_argument("--date", help="发布日期 YYYY-MM-DD，默认北京时间当天")
    parser.add_argument("--from-bank", action="store_true", help="从未使用的备用内容组中发布")
    parser.add_argument("--replace", action="store_true", help="允许替换已有日期")
    parser.add_argument("--check", action="store_true", help="只校验现有data.json")
    args = parser.parse_args()

    db = load_json(DATA_PATH)
    if args.check:
        validate_database(db)
        print(f"OK: {len(db.get('data', {}))} days")
        return

    date = args.date or datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
    datetime.strptime(date, "%Y-%m-%d")
    if date in db.get("data", {}) and not args.replace:
        print(f"SKIP: {date} already exists")
        return
    if args.from_bank:
        items = items_from_bank(date, db)
    elif args.input:
        items = normalize_items(load_json(args.input), date)
    else:
        raise ValueError("必须提供--input或--from-bank")
    reject_near_duplicates(items, db)
    db.setdefault("data", {})[date] = items
    now = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M")
    db["updated_at"] = now
    validate_database(db)
    DATA_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"UPDATED: {date} with {len(items)} items at {now}")


if __name__ == "__main__":
    main()
