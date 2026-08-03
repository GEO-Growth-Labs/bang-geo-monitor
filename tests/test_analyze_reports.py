from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "skills" / "bang" / "scripts" / "analyze_reports.py"
SPEC = importlib.util.spec_from_file_location("bang_analyze_reports", MODULE_PATH)
assert SPEC and SPEC.loader
ANALYZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYZER)


class KeywordAnalysisTests(unittest.TestCase):
    def test_sorts_weak_and_small_advantage_keywords(self):
        rows = [
            ["", "", "示例品牌(客户)", "竞品甲(核心竞品)", "竞品乙(核心竞品)"],
            ["关键词名称", "AI平台名称", "AI平台的可见占比", "AI平台的可见占比", "AI平台的可见占比"],
            ["示例关键词A", "豆包", 0.2, 0.4, 0.6],
            ["示例关键词A", "Kimi", 0.4, 0.6, 0.8],
            ["示例关键词B", "豆包", "55%", "50%", "50%"],
            ["示例关键词B", "Kimi", 0.55, 0.50, 0.50],
            ["示例关键词C", "豆包", 0.51, 0.50, 0.50],
            ["示例关键词C", "Kimi", 0.51, 0.50, 0.50],
            ["示例关键词D", "豆包", 0.30, 0.30, 0.30],
        ]

        weak, advantage = ANALYZER.analyze_keyword_rows(rows)

        self.assertEqual([item["keyword"] for item in weak], ["示例关键词A"])
        self.assertAlmostEqual(weak[0]["gap"], 0.3)
        self.assertEqual(
            [item["keyword"] for item in advantage],
            ["示例关键词C", "示例关键词B"],
        )
        self.assertAlmostEqual(advantage[0]["advantage"], 0.01)
        self.assertAlmostEqual(advantage[1]["advantage"], 0.05)

    def test_requires_explicit_customer_and_competitor_markers(self):
        rows = [
            ["", "", "品牌A", "品牌B"],
            ["关键词名称", "AI平台名称", "AI平台的可见占比", "AI平台的可见占比"],
            ["示例关键词", "豆包", 0.2, 0.3],
        ]
        with self.assertRaisesRegex(ValueError, "customer visibility"):
            ANALYZER.analyze_keyword_rows(rows)


class SourceAnalysisTests(unittest.TestCase):
    def test_aggregates_normalizes_and_uses_full_platform_total(self):
        reports = [
            [
                ["信源平台名称", "AI平台名称", "AI平台的信源文章数"],
                ["sohu.com", "豆包", 6],
                ["搜狐", "豆包", 4],
                ["example-a.invalid", "豆包", 5],
                ["sohu.com", "DeepSeek", 3],
            ],
            [
                ["信源平台名称", "AI平台名称", "AI平台的信源文章数"],
                ["www.sohu.com", "豆包", 2],
                ["example-b.invalid", "豆包", 8],
                ["sohu.com", "DeepSeek", 7],
            ],
        ]
        aliases = ANALYZER.load_aliases(ROOT / "skills" / "bang" / "references" / "source-aliases.json")

        rankings, appearances = ANALYZER.analyze_source_rows(reports, aliases, top_n=2)

        self.assertEqual(rankings["豆包"][0]["source"], "搜狐网")
        self.assertEqual(rankings["豆包"][0]["article_count"], 12)
        self.assertAlmostEqual(rankings["豆包"][0]["share"], 12 / 25)
        self.assertEqual(rankings["DeepSeek"][0]["article_count"], 10)
        self.assertEqual(appearances["搜狐网"], 2)

    def test_rejects_negative_counts(self):
        reports = [[
            ["信源平台名称", "AI平台名称", "AI平台的信源文章数"],
            ["example.invalid", "豆包", -1],
        ]]
        rankings, _ = ANALYZER.analyze_source_rows(reports, {}, top_n=20)
        self.assertEqual(rankings["豆包"], [])


class AliasTests(unittest.TestCase):
    def test_alias_file_is_valid_json_string_map(self):
        path = ROOT / "skills" / "bang" / "references" / "source-aliases.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(data)
        self.assertTrue(all(isinstance(key, str) and isinstance(value, str) for key, value in data.items()))


if __name__ == "__main__":
    unittest.main()
