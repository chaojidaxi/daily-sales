import json
import tempfile
import unittest
from pathlib import Path
from scripts.update_data import CATEGORIES, normalize_items, reject_near_duplicates


class UpdateDataTests(unittest.TestCase):
    def sample(self):
        return [{
            "category": category,
            "audience": "全员",
            "title": f"这是第{i}条有效销售提醒",
            "content": "顾客表达需求以后，先确认她真正关注的使用场景，不要急着把所有卖点一次讲完。推荐的价值不是信息越多越好，而是帮助顾客降低判断难度。先听懂她在意版型、场合还是预算，再给出少量清楚的选择。每介绍一个款，都要说明它为什么适合眼前这个人。顾客感到被理解，才愿意继续试穿和比较。",
            "example": "可以这样问：您今天更想解决上班穿搭，还是周末出门的搭配？",
            "action": "今天选择一次完整接待，先确认场景和在意点，再开始推荐。",
        } for i, category in enumerate(CATEGORIES, 1)]

    def test_normalizes_five_categories(self):
        items = normalize_items(self.sample(), "2026-08-17")
        self.assertEqual(5, len(items))
        self.assertEqual("20260817-01", items[0]["id"])
        self.assertEqual(set(CATEGORIES), {x["category"] for x in items})

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


if __name__ == "__main__":
    unittest.main()
