from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SkillMetadataTests(unittest.TestCase):
    def test_skill_frontmatter_has_only_name_and_description(self):
        content = (ROOT / "skills" / "bang" / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        self.assertIsNotNone(match)
        keys = [line.split(":", 1)[0] for line in match.group(1).splitlines() if ":" in line]
        self.assertEqual(keys, ["name", "description"])
        self.assertIn("Default to the latest 10", match.group(1))
        self.assertIn("zero, negative, decimal, or malformed", content)
        self.assertIn("exceeds available generated tasks", content)

    def test_openai_yaml_mentions_skill_in_default_prompt(self):
        content = (ROOT / "skills" / "bang" / "agents" / "openai.yaml").read_text(encoding="utf-8")
        private_address = ".".join(("8", "141", "17", "133"))
        self.assertIn("$bang", content)
        self.assertIn('value: "wanhu-admin"', content)
        self.assertNotIn(private_address, content)


if __name__ == "__main__":
    unittest.main()
