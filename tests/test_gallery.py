"""Checks gallery/gallery.json, the data file the gallery website reads."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GALLERY = ROOT / "gallery" / "gallery.json"
MAX_SCREENSHOT = 1_000_000


class Gallery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(GALLERY.read_text(encoding="utf-8"))
        cls.items = cls.data["items"]
        cls.categories = {c["id"] for c in cls.data["categories"]}
        cls.styles = {i["id"][len("profile-"):] for i in cls.items if i["category"] == "profiles"} | {"project"}

    def test_asset_base_is_jsdelivr(self):
        self.assertRegex(self.data["assetBase"], r"^https://cdn\.jsdelivr\.net/gh/tanmayai23/README-Editor-skill@[\w.-]+/$")

    def test_ids_are_unique(self):
        ids = [i["id"] for i in self.items]
        self.assertEqual(len(ids), len(set(ids)), [x for x in ids if ids.count(x) > 1])

    def test_every_item_is_complete(self):
        for it in self.items:
            with self.subTest(it.get("id")):
                for key in ("id", "category", "title", "description", "image", "animated", "link", "source"):
                    self.assertIn(key, it)
                self.assertIn(it["category"], self.categories)
                self.assertIn(it["source"], ("official", "community"))
                self.assertIsInstance(it["animated"], bool)
                self.assertTrue(it["title"].strip() and it["description"].strip())
                self.assertNotIn("{{", it["title"] + it["description"])

    def test_images_exist(self):
        for it in self.items:
            if it["image"] is None:
                continue
            for theme in ("dark", "light"):
                with self.subTest(it["id"], theme=theme):
                    p = ROOT / it["image"][theme]
                    self.assertTrue(p.is_file(), p)

    def test_official_links_exist(self):
        for it in self.items:
            if it["source"] == "official":
                with self.subTest(it["id"]):
                    self.assertTrue((ROOT / it["link"].split("#")[0]).is_file(), it["link"])
                    self.assertTrue(it.get("command"))

    def test_community_entries(self):
        for it in self.items:
            if it["source"] != "community":
                continue
            with self.subTest(it["id"]):
                self.assertEqual(it["category"], "community")
                self.assertTrue(it["id"].startswith("community-"))
                self.assertRegex(it["link"], r"^https://")
                self.assertIn(it.get("style"), self.styles)
                self.assertRegex(it["author"]["github"], r"^[A-Za-z0-9-]{1,39}$")
                self.assertTrue(it["author"]["name"].strip())
                self.assertIsNotNone(it["image"])
                for theme in ("dark", "light"):
                    p = ROOT / it["image"][theme]
                    self.assertTrue(p.as_posix().startswith((ROOT / "gallery" / "screenshots").as_posix()), p)
                    self.assertRegex(p.name, r"\.(png|webp|jpg|jpeg|gif)$")
                    self.assertLessEqual(p.stat().st_size, MAX_SCREENSHOT, f"{p.name} is over 1 MB")

    def test_counts_match_the_repo(self):
        banners = sorted(p.name[: -len("-dark.svg")] for p in (ROOT / "readme-forge-design/assets/banners").glob("*-dark.svg")
                         if not re.match(r"(footer|divider|button)-", p.name))
        self.assertEqual(sorted(i["title"] for i in self.items if i["category"] == "banners"), banners)
        profiles = sorted(p.stem for p in (ROOT / "readme-forge-design/templates/profile").glob("*.md"))
        self.assertEqual(sorted(i["id"][len("profile-"):] for i in self.items if i["category"] == "profiles"), profiles)


if __name__ == "__main__":
    unittest.main()
