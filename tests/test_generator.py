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
            "title": f"这是第{i}条一批销售提醒",
            "content": "一批档口销售接到拿货客户询问时，先确认对方所在区域、经营渠道和目标价格带。不要急着把所有新款一次发完，否则客户很难判断重点。先根据她的客群定位筛出一组主推款，再说明每个款适合怎样的下游门店。报价时同时讲清起批要求、现货情况和补单节奏。客户获得的是一套可判断的组货方案，而不是零散图片。信息越贴近她的生意，后续看版和返单越容易推进。",
            "example": "可以这样问：您这次主要补哪个价格带，门店款和电商款各需要多少？",
            "action": "今天由批发销售整理一位重点客户的区域、渠道和价格带后再推荐。",
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

    def test_rejects_retail_scenario(self):
        bad = self.sample()
        bad[0]["example"] = "顾客进店以后先邀请试穿，再根据身材介绍适合的日常穿搭。"
        with self.assertRaisesRegex(ValueError, "零售化场景词"):
            normalize_items(bad, "2026-08-17")


if __name__ == "__main__":
    unittest.main()
