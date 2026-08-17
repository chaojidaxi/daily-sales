#!/usr/bin/env python3
"""Validate and append one day's sales-growth content to data.json."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

CATEGORIES = [
    "销售认知", "批发技巧", "客户经营", "执行心态",
    "服务履约", "团队协作", "店长管理", "销售复盘",
]
AUDIENCES = {"老板/主理人", "店长", "批发销售", "全员", "老板/店长", "店长/批发销售"}
WHOLESALE_TERMS = {
    "一批", "批发", "档口", "拿货", "看版", "选款", "组货", "报价", "起批",
    "补单", "返单", "动销", "发货", "库存", "订货会", "买手", "连锁客户",
    "电商客户", "店老板", "价格带", "区域市场", "采购预算", "下游门店",
}
RETAIL_PHRASES = {
    "顾客进店", "接待顾客", "邀请试穿", "试穿", "上班穿", "聚会穿", "日常穿",
    "身材", "腰部", "穿搭推荐", "连带销售", "零售门店",
}
ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data.json"
BANK_PATH = ROOT / "content_bank.json"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_items(raw, date: str):
    items = raw.get("items", raw) if isinstance(raw, dict) else raw
    if not isinstance(items, list) or len(items) != len(CATEGORIES):
        raise ValueError("每天必须正好8条内容，每个分类1条")
    seen_categories, seen_titles, clean = set(), set(), []
    for idx, item in enumerate(items, 1):
        if not isinstance(item, dict):
            raise ValueError(f"第{idx}条不是对象")
        missing = {"category", "audience", "title", "content", "example", "action"} - set(item)
        if missing:
            raise ValueError(f"第{idx}条缺少字段: {sorted(missing)}")
        category = str(item["category"]).strip()
        audience = str(item["audience"]).strip()
        title = str(item["title"]).strip()
        content = re.sub(r"\s+", " ", str(item["content"]).strip())
        example = re.sub(r"\s+", " ", str(item["example"]).strip())
        action = re.sub(r"\s+", " ", str(item["action"]).strip())
        if category not in CATEGORIES:
            raise ValueError(f"第{idx}条分类不正确: {category}")
        if audience not in AUDIENCES:
            raise ValueError(f"第{idx}条对象不正确: {audience}")
        if not 8 <= len(title) <= 16:
            raise ValueError(f"第{idx}条标题长度应为8-16字")
        if not 70 <= len(content) <= 115:
            raise ValueError(f"第{idx}条正文长度应为70-115字")
        sentence_count = len(re.findall(r"[。！？]", content))
        if not 3 <= sentence_count <= 5:
            raise ValueError(f"第{idx}条正文应包含3-5个完整短句")
        if not 20 <= len(example) <= 45:
            raise ValueError(f"第{idx}条现场表达长度应为20-45字")
        if not 15 <= len(action) <= 32:
            raise ValueError(f"第{idx}条行动长度应为15-32字")
        total_length = sum(map(len, (title, content, example, action)))
        if not 150 <= total_length <= 220:
            raise ValueError(f"第{idx}条总长度应为150-220字，当前{total_length}字")
        combined_text = title + content + example + action
        retail_hits = sorted(phrase for phrase in RETAIL_PHRASES if phrase in combined_text)
        if retail_hits:
            raise ValueError(f"第{idx}条出现零售化场景词: {retail_hits}")
        if not any(term in combined_text for term in WHOLESALE_TERMS):
            raise ValueError(f"第{idx}条缺少服装一批业务场景词")
        if title in seen_titles:
            raise ValueError(f"标题重复: {title}")
        seen_titles.add(title)
        seen_categories.add(category)
        clean.append({
            "id": f"{date.replace('-', '')}-{idx:02d}", "category": category,
            "audience": audience, "title": title, "content": content,
            "example": example, "action": action,
        })
    missing_categories = set(CATEGORIES) - seen_categories
    if missing_categories:
        raise ValueError(f"每天必须覆盖8个分类，缺少: {sorted(missing_categories)}")
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
    if int(db.get("daily_minimum", 0)) != 8:
        raise ValueError("daily_minimum必须等于8")
    for date, items in db.get("data", {}).items():
        datetime.strptime(date, "%Y-%m-%d")
        normalize_items(items, date)
    return True


def validate_bank(bank):
    if not isinstance(bank, list) or not bank:
        raise ValueError("备用内容库必须是非空数组")
    groups, titles = {}, []
    for item in bank:
        if "bank_day" not in item:
            raise ValueError("备用内容缺少bank_day")
        groups.setdefault(int(item["bank_day"]), []).append(item)
        titles.append(str(item.get("title", "")).strip())
    if len(titles) != len(set(titles)):
        raise ValueError("备用内容库存在重复标题")
    for day, items in sorted(groups.items()):
        if len(items) != 8:
            raise ValueError(f"备用第{day}组不是8篇")
        normalize_items(items, f"2099-01-{day:02d}" if day <= 31 else "2099-01-31")
    return len(groups)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, help="包含当日8条内容的JSON文件")
    parser.add_argument("--date", help="发布日期 YYYY-MM-DD，默认北京时间当天")
    parser.add_argument("--from-bank", action="store_true", help="从未使用的备用内容组中发布")
    parser.add_argument("--replace", action="store_true", help="允许替换已有日期")
    parser.add_argument("--check", action="store_true", help="只校验现有data.json")
    args = parser.parse_args()

    db = load_json(DATA_PATH)
    if args.check:
        validate_database(db)
        bank_groups = validate_bank(load_json(BANK_PATH))
        print(f"OK: {len(db.get('data', {}))} published days / {bank_groups} wholesale bank groups")
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
