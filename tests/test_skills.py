"""Both SKILL.md files must fit the limits claude.ai enforces when a skill zip is uploaded."""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = ["readme-forge", "readme-forge-design"]


def frontmatter(skill):
    with open(os.path.join(ROOT, skill, "SKILL.md"), encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    assert m, skill + "/SKILL.md has no frontmatter"
    fields = {}
    for line in m.group(1).split("\n"):
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


class SkillFrontmatterTest(unittest.TestCase):
    def test_name_matches_folder(self):
        for skill in SKILLS:
            name = frontmatter(skill)["name"]
            self.assertEqual(name, skill)
            self.assertRegex(name, r"^[a-z0-9-]{1,64}$")

    def test_description_fits_upload_limit(self):
        for skill in SKILLS:
            desc = frontmatter(skill)["description"]
            self.assertTrue(desc, skill)
            self.assertLessEqual(len(desc), 1024, skill + " description is %d characters" % len(desc))
            self.assertNotRegex(desc, r"<[A-Za-z/]", skill + " description has an XML tag")


if __name__ == "__main__":
    unittest.main()
