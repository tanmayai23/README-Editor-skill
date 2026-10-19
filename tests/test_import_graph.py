"""Fixture-backed tests for readme-forge/scripts/import_graph.py.

Fixtures live in tests/fixtures/imports/<lang>/ with known imports; each test
asserts the exact edge set, so a missing edge or a spurious one both fail.
"""
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "readme-forge" / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "imports"
sys.path.insert(0, str(SCRIPTS))

import import_graph  # noqa: E402


def graph(name, depth=0):
    return import_graph.build(FIXTURES / name, depth)


class PythonImportsTest(unittest.TestCase):
    def test_file_level_edges(self):
        edges, _, ext_edges, groups = graph("python")
        self.assertEqual(set(edges), {
            ("main", "pkg/api/routes"),        # from pkg.api import routes  (submodule, not pkg/api/__init__)
            ("main", "pkg/core"),              # import pkg.core
            ("pkg/core", "pkg/utils"),         # from . import utils  (#31: used to point at pkg/__init__)
            ("pkg/core", "pkg/models"),        # from .models import User
            ("pkg/models", "pkg/utils"),       # from .utils import helper
            ("pkg/api/routes", "pkg/core"),    # from ..core import run
            ("pkg/api/routes", "pkg/models"),  # from pkg.models import User
        })
        self.assertNotIn(("pkg/core", "pkg/__init__"), edges)
        self.assertEqual(set(ext_edges), {("pkg/api/routes", "http")})  # import requests
        self.assertIn("pkg/__init__", groups)

    def test_package_level_edges(self):
        edges, _, _, _ = graph("python", depth=2)
        self.assertEqual(set(edges), {("main", "pkg"), ("main", "pkg/api"), ("pkg/api", "pkg")})


class JsTsImportsTest(unittest.TestCase):
    def test_file_level_edges(self):
        edges, _, ext_edges, groups = graph("js-ts")
        self.assertEqual(set(edges), {
            ("index", "lib/greet"),      # "@lib/greet" via tsconfig paths (file has // comments)
            ("index", "app"),            # './app' -> app.tsx
            ("index", "lib/format"),     # './lib/format.js' -> format.ts (ESM TS style)
            ("index", "util"),           # require('./util')
            ("app", "lib/index"),        # './lib' -> lib/index.ts
            ("app", "lib/format"),       # '@lib/format'
            ("lib/index", "lib/greet"),  # export { } from './greet'
            ("lib/greet", "lib/format"),
            ("util", "lib/format"),
        })
        self.assertNotIn("app.test", groups)  # test files are excluded
        self.assertEqual(set(ext_edges), {("util", "http")})  # axios

    def test_tsconfig_aliases(self):
        aliases = import_graph.tsconfig_aliases(FIXTURES / "js-ts")
        self.assertEqual(aliases["@lib"], "src/lib")


class GoImportsTest(unittest.TestCase):
    def test_package_level_edges(self):
        edges, _, ext_edges, groups = graph("go", depth=2)
        self.assertEqual(set(edges), {
            ("main", "internal/store"),
            ("main", "pkg/api"),
            ("pkg/api", "internal/store"),
            ("cmd/tool", "pkg/api"),
        })
        self.assertEqual(set(ext_edges), {("internal/store", "db")})  # database/sql
        self.assertEqual(groups["pkg/api"], 2)  # api.go + handler.go; store_test.go excluded

    def test_go_mod_in_subfolder(self):
        edges, _, _, _ = graph("go-submodule")
        self.assertEqual(set(edges), {("backend/main", "backend/internal/db/db")})


class RustImportsTest(unittest.TestCase):
    def test_file_level_edges(self):
        edges, _, _, _ = graph("rust")
        self.assertEqual(set(edges), {
            ("main", "config"),          # mod config;
            ("main", "net/mod"),         # mod net;
            ("main", "net/client"),      # use crate::net::client::Client
            ("net/mod", "net/client"),   # pub mod client;  (resolved next to net/mod.rs)
            ("net/mod", "config"),       # use crate::config::Settings
            ("net/client", "config"),
        })


class MermaidOutputTest(unittest.TestCase):
    def test_to_mermaid_starts_with_flowchart(self):
        edges, externals, ext_edges, groups = graph("go", depth=2)
        out = import_graph.to_mermaid(edges, externals, ext_edges, groups, 14)
        self.assertTrue(out.startswith("flowchart"))
        self.assertIn("pkg_api --> internal_store", out)
        self.assertIn('ext_db[("SQL Database")]', out)

    def test_cli_mermaid_flag(self):
        for name in ("python", "js-ts", "go", "rust"):
            with self.subTest(fixture=name):
                res = subprocess.run([sys.executable, str(SCRIPTS / "import_graph.py"), str(FIXTURES / name), "--mermaid"],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                lines = [l for l in res.stdout.decode("utf-8").splitlines() if not l.startswith("%%")]
                self.assertEqual(lines[0], "```mermaid")
                self.assertTrue(lines[1].startswith("flowchart"), lines[1])
                self.assertEqual(lines[-1], "```")


if __name__ == "__main__":
    unittest.main()
