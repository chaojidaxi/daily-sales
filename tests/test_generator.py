import json
import tempfile
import unittest
from pathlib import Path
from scripts.update_data import CATEGORIES, normalize_items, reject_near_duplicates


EXPECTED_CATEGORIES = [
    "销售认知", "批发技巧", "客户经营", "执行心态",
    "服务履约", "团队协作", "店长管理", "销售复盘",
]


class UpdateDataTests(unittest.TestCase):
    def sample(self):
        return [{
            "category": category,
            "audience": "全员",
            "title": f"一批销售第{i}个关键动作",
            "content": "拿货客户看版后没回复，不一定是没有需求，也可能是款太多、重点不清。批发销售不要继续机械发图，应按客户渠道和价格带重新筛款。再说明每个款在货盘里的作用，客户才更容易判断。让推荐从发款变成帮助客户做采购判断。",
            "example": "我按您的价格带重选了几个款，并把组货理由一起发您。",
            "action": "今天找三位未回复客户，各做一次精选推荐。",
        } for i, category in enumerate(EXPECTED_CATEGORIES, 1)]

    def test_normalizes_eight_required_categories(self):
        items = normalize_items(self.sample(), "2026-08-17")
        self.assertEqual(EXPECTED_CATEGORIES, CATEGORIES)
        self.assertEqual(8, len(items))
        self.assertEqual("20260817-01", items[0]["id"])
        self.assertEqual(set(EXPECTED_CATEGORIES), {x["category"] for x in items})
        self.assertTrue(all(150 <= sum(len(x[k]) for k in ("title", "content", "example", "action")) <= 220 for x in items))

    def test_rejects_missing_category(self):
        bad = self.sample()
        bad[-1]["category"] = "销售认知"
        with self.assertRaisesRegex(ValueError, "缺少"):
            normalize_items(bad, "2026-08-17")

    def test_rejects_history_duplicate(self):
        items = normalize_items(self.sample(), "2026-08-17")
        db = {"data": {"2026-08-16": [dict(items[0], id="old")]}}
        with self.assertRaisesRegex(ValueError, "过于相似"):
            reject_near_duplicates(items, db)

    def test_rejects_retail_scenario(self):
        bad = self.sample()
        bad[0]["example"] = "顾客进店以后先邀请试穿，再根据身材介绍适合的日常穿搭。"
        with self.assertRaisesRegex(ValueError, "零售化场景词"):
            normalize_items(bad, "2026-08-17")


if __name__ == "__main__":
    unittest.main()
