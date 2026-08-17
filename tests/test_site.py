import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SiteContractTests(unittest.TestCase):
    def test_homepage_lists_all_eight_categories(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        expected = [
            "销售认知", "批发技巧", "客户经营", "执行心态",
            "服务履约", "团队协作", "店长管理", "销售复盘",
        ]
        for category in expected:
            self.assertIn(category, html)
        self.assertIn("每天固定更新8类", html)

    def test_homepage_has_no_evening_review_or_live_generator(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("晚上复盘", html)
        self.assertNotIn("输入实际问题生成", html)


if __name__ == "__main__":
    unittest.main()
