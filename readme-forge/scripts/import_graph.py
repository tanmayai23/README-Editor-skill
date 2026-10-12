#!/usr/bin/env python3
"""Build a module-level dependency graph from real imports and emit a Mermaid draft.

Stdlib only. Supports Python, JavaScript/TypeScript, Go, Rust (mod/use crate::).
Usage:
    python import_graph.py <repo_path> [--mermaid] [--json] [--depth N] [--max-nodes N]

--depth N      group files by their first N path segments under the source root (default 2; 0 = one node per file)
--files        force file-level nodes (automatic when fewer than 4 packages are found)
--max-nodes N  keep the N most connected groups (default 14)

The output is a DRAFT: rename nodes to human terms, add external systems
(DB, queue, third-party APIs) found in the code, and label edges with verbs.
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

IGNORE_DIRS = {
    ".git", "node_modules", ".venv", "venv", "env", "__pycache__", "dist", "build", "target",
    ".next", ".nuxt", "out", "coverage", ".tox", "vendor", ".turbo", ".cache", "site-packages",
    "migrations", ".svelte-kit", "public", "static", "assets",
}
TEST_RE = re.compile(r"(^|/)(tests?|__tests__|spec|e2e|fixtures|mocks?)(/|$)|(_test\.go|\.test\.[jt]sx?|\.spec\.[jt]sx?|^test_.*\.py|conftest\.py)$")
CONFIG_RE = re.compile(r"^\.|\.config\.[cm]?[jt]s$|^(setup|conftest|noxfile|fabfile|gulpfile|gruntfile|webpack\..*|rollup\..*|babel\..*|jest\..*|vite\..*|vitest\..*|eslint\..*|prettier\..*|tailwind\..*|postcss\..*|next\.config.*|nuxt\.config.*|svelte\.config.*|astro\.config.*|playwright\..*|openapi-ts\..*)(\.[\w]+)?$", re.I)
CODE_EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".rs", ".vue", ".svelte"}

PY_IMPORT = re.compile(r"^\s*(?:from\s+(\.*[\w.]*)\s+import\s+([\w*, ()]+)|import\s+([\w., ]+))", re.M)
JS_IMPORT = re.compile(r"""(?:import\s+(?:[^'"]*?\s+from\s+)?|export\s+[^'"]*?\s+from\s+|require\(\s*|import\(\s*)['"]([^'"]+)['"]""")
GO_IMPORT_BLOCK = re.compile(r"import\s*\(([^)]*)\)", re.S)
GO_IMPORT_ONE = re.compile(r'import\s+(?:\w+\s+)?"([^"]+)"')
RS_USE = re.compile(r"^\s*(?:pub\s+)?(?:use|mod)\s+(crate::)?([\w:]+)", re.M)

EXTERNAL_HINTS = {
    # import name fragment -> (node id, label, shape)
    "sqlalchemy": ("db", "Database", "db"), "psycopg": ("db", "PostgreSQL", "db"), "pg": ("db", "PostgreSQL", "db"),
    "prisma": ("db", "Database (Prisma)", "db"), "mongoose": ("db", "MongoDB", "db"), "pymongo": ("db", "MongoDB", "db"),
    "redis": ("cache", "Redis", "db"), "ioredis": ("cache", "Redis", "db"), "sqlite3": ("db", "SQLite", "db"),
    "drizzle-orm": ("db", "Database (Drizzle)", "db"), "gorm.io": ("db", "Database (GORM)", "db"), "database/sql": ("db", "SQL Database", "db"),
    "typeorm": ("db", "Database (TypeORM)", "db"), "sequelize": ("db", "Database (Sequelize)", "db"),
    "boto3": ("aws", "AWS", "ext"), "@aws-sdk": ("aws", "AWS", "ext"), "stripe": ("stripe", "Stripe API", "ext"),
    "openai": ("llm", "LLM API", "ext"), "anthropic": ("llm", "LLM API", "ext"), "@anthropic-ai/sdk": ("llm", "LLM API", "ext"),
    "celery": ("queue", "Task queue", "queue"), "bullmq": ("queue", "Job queue", "queue"), "kafka": ("queue", "Kafka", "queue"),
    "pika": ("queue", "RabbitMQ", "queue"), "amqplib": ("queue", "RabbitMQ", "queue"),
    "@supabase/supabase-js": ("supabase", "Supabase", "ext"), "firebase": ("firebase", "Firebase", "ext"),
    "requests": ("http", "External HTTP APIs", "ext"), "httpx": ("http", "External HTTP APIs", "ext"), "axios": ("http", "External HTTP APIs", "ext"),
    "torch": ("model", "PyTorch model", "ext"), "transformers": ("model", "HF Transformers", "ext"),
    "s3": ("aws", "AWS", "ext"), "elasticsearch": ("search", "Elasticsearch", "db"),
}


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")[:300_000]
    except OSError:
        return ""


def source_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".")]
        for n in filenames:
            p = Path(dirpath) / n
            if p.suffix in CODE_EXT:
                r = p.relative_to(root).as_posix()
                if not TEST_RE.search(r) and not n.endswith(".d.ts") and not CONFIG_RE.search(n):
                    yield p, r


def source_root(root: Path) -> Path:
    for cand in ("src", "lib", "app"):
        d = root / cand
        if d.is_dir() and sum(1 for _ in d.rglob("*") if _.suffix in CODE_EXT) >= 3:
            return d
    return root


def group_of(relpath: str, depth: int, prefix: str) -> str:
    if prefix and relpath.startswith(prefix + "/"):
        relpath = relpath[len(prefix) + 1:]
    parts = relpath.split("/")
    if depth == 0:  # file-level mode
        stem = str(Path(relpath).with_suffix("")).replace("\\", "/")
        return stem
    if len(parts) == 1:
        stem = Path(parts[0]).stem
        return stem if stem not in ("index", "__init__", "mod", "lib") else "(root)"
    seg = parts[:-1][:depth]
    return "/".join(seg)


def resolve_js(spec: str, src: str, files: set, aliases: dict):
    for a, target in aliases.items():
        if spec == a or spec.startswith(a + "/"):
            spec = target + spec[len(a):]
            base = ""
            break
    else:
        if not spec.startswith("."):
            return None
        base = str(Path(src).parent.as_posix())
    cand = os.path.normpath(os.path.join(base, spec)).replace("\\", "/").lstrip("./") if base else spec.lstrip("/")
    for ext in ("", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".vue", ".svelte", "/index.ts", "/index.tsx", "/index.js"):
        if cand + ext in files:
            return cand + ext
    # strip .js -> .ts (ESM TS style)
    if cand.endswith(".js") and cand[:-3] + ".ts" in files:
        return cand[:-3] + ".ts"
    return None


def resolve_py(mod: str, src: str, files: set, pkg_roots: list):
    if mod.startswith("."):
        dots = len(mod) - len(mod.lstrip("."))
        base = Path(src).parent
        for _ in range(dots - 1):
            base = base.parent
        rest = mod.lstrip(".").replace(".", "/")
        cand = (base / rest).as_posix() if rest else base.as_posix()
        cand = cand.lstrip("./")
        for c in (cand + ".py", cand + "/__init__.py"):
            if c in files:
                return c
        return None
    path = mod.replace(".", "/")
    for r in pkg_roots:
        pre = f"{r}/" if r else ""
        for c in (f"{pre}{path}.py", f"{pre}{path}/__init__.py"):
            if c in files:
                return c
    # parent module (from pkg.mod import name where name is a symbol)
    if "/" in path:
        return resolve_py(mod.rsplit(".", 1)[0], src, files, pkg_roots)
    return None


def tsconfig_aliases(root: Path) -> dict:
    aliases = {}
    for name in ("tsconfig.json", "jsconfig.json"):
        p = root / name
        if not p.exists():
            continue
        txt = re.sub(r"//.*|/\*.*?\*/", "", read(p), flags=re.S)
        txt = re.sub(r",(\s*[}\]])", r"\1", txt)
        try:
            data = json.loads(txt)
        except ValueError:
            continue
        opts = data.get("compilerOptions") or {}
        base = (opts.get("baseUrl") or ".").strip("./")
        for k, v in (opts.get("paths") or {}).items():
            if v:
                a = k.rstrip("/*")
                t = v[0].rstrip("/*").lstrip("./")
                aliases[a] = "/".join(x for x in (base, t) if x)
    if (root / "src").is_dir():
        aliases.setdefault("@", "src")
        aliases.setdefault("~", "src")
    return aliases


def build(root: Path, depth: int):
    root = root.resolve()
    rels = {r: p for p, r in source_files(root)}
    fileset = set(rels)
    aliases = tsconfig_aliases(root)
    pkg_roots = ["", "src", "lib", "app"]
    # Python sub-projects (monorepo backends): imports resolve relative to the dir holding pyproject/setup.py
    for sub in sorted(root.glob("*/")) + sorted(root.glob("*/*/")):
        if sub.is_dir() and sub.name not in IGNORE_DIRS and any((sub / m).exists() for m in ("pyproject.toml", "setup.py", "requirements.txt")):
            r_ = sub.relative_to(root).as_posix()
            pkg_roots += [r_, f"{r_}/src"]
        for js in ("tsconfig.json", "jsconfig.json"):
            if sub.is_dir() and (sub / js).exists() and sub.name not in IGNORE_DIRS:
                for a, t in tsconfig_aliases(sub).items():
                    aliases.setdefault(a, f"{sub.relative_to(root).as_posix()}/{t}")
    go_mod = ""
    gm = root / "go.mod"
    if gm.exists():
        m = re.search(r"^module\s+(\S+)", read(gm), re.M)
        go_mod = m.group(1) if m else ""
    sroot = source_root(root)
    prefix = sroot.relative_to(root).as_posix() if sroot != root else ""
    if not prefix and len(pkg_roots) > 4 and depth == 2:
        depth = 3  # monorepo without src/: group one level deeper (backend/app/api)

    edges = Counter()
    externals = {}
    ext_edges = Counter()
    group_files = defaultdict(int)

    for r, p in rels.items():
        g_src = group_of(r, depth, prefix)
        group_files[g_src] += 1
        txt = read(p)
        targets = []
        externals_seen = []
        if p.suffix == ".py":
            for frm, names_, imp in PY_IMPORT.findall(txt):
                mods = [frm] if frm else [m.strip().split(" as ")[0] for m in imp.split(",")]
                for m in mods:
                    if not m:
                        continue
                    t = resolve_py(m, r, fileset, pkg_roots)
                    if t:
                        targets.append(t)
                    else:
                        externals_seen.append(m.split(".")[0])
        elif p.suffix in (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte"):
            for spec in JS_IMPORT.findall(txt):
                t = resolve_js(spec, r, fileset, aliases)
                if t:
                    targets.append(t)
                elif not spec.startswith("."):
                    externals_seen.append(spec if spec.startswith("@") and "/" in spec and spec.split("/")[0] in ("@anthropic-ai", "@supabase", "@aws-sdk") else spec.split("/")[0])
        elif p.suffix == ".go":
            specs = GO_IMPORT_ONE.findall(txt)
            for block in GO_IMPORT_BLOCK.findall(txt):
                specs += re.findall(r'"([^"]+)"', block)
            for s in specs:
                if go_mod and s.startswith(go_mod + "/"):
                    d = s[len(go_mod) + 1:]
                    cands = [f for f in fileset if f.startswith(d + "/") and f.count("/") == d.count("/") + 1]
                    if cands:
                        targets.append(sorted(cands)[0])
                else:
                    externals_seen.append(s)
        elif p.suffix == ".rs":
            for crate, path in RS_USE.findall(txt):
                first = path.split("::")[0]
                for c in (f"src/{first}.rs", f"src/{first}/mod.rs"):
                    if c in fileset:
                        targets.append(c)
                        break
        for t in targets:
            g_dst = group_of(t, depth, prefix)
            if g_dst != g_src:
                edges[(g_src, g_dst)] += 1
        for e in externals_seen:
            for hint, (nid, label, shape) in EXTERNAL_HINTS.items():
                if e == hint or e.startswith(hint):
                    externals[nid] = (label, shape)
                    ext_edges[(g_src, nid)] += 1
                    break
    return edges, externals, ext_edges, group_files


def node_id(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]", "_", name).strip("_") or "root"
    reserved = {"end", "graph", "subgraph", "flowchart", "style", "class", "classdef", "click", "default", "linkstyle", "direction"}
    return ("n_" + s) if s[0].isdigit() or s.lower() in reserved else s


def to_mermaid(edges, externals, ext_edges, group_files, max_nodes: int) -> str:
    degree = Counter()
    for (a, b), w in edges.items():
        degree[a] += w
        degree[b] += w
    for (a, _), w in ext_edges.items():
        degree[a] += w
    for g, n in group_files.items():
        degree[g] += 0.01 * n
    keep = {g for g, _ in degree.most_common(max_nodes)}
    lines = ["flowchart LR"]
    # subgraph by top-level segment
    by_top = defaultdict(list)
    for g in sorted(keep):
        by_top[g.split("/")[0]].append(g)
    for top, groups in by_top.items():
        if len(groups) > 1:
            lines.append(f'    subgraph {node_id("sg_" + top)}["{top}"]')
            for g in groups:
                lines.append(f'        {node_id(g)}["{g.split("/")[-1]}"]')
            lines.append("    end")
        else:
            g = groups[0]
            lines.append(f'    {node_id(g)}["{g}"]')
    for nid, (label, shape) in sorted(externals.items()):
        if not any(a in keep for (a, n) in ext_edges if n == nid):
            continue
        if shape == "db":
            lines.append(f'    ext_{nid}[("{label}")]')
        elif shape == "queue":
            lines.append(f'    ext_{nid}[["{label}"]]')
        else:
            lines.append(f'    ext_{nid}{{{{"{label}"}}}}')
    for (a, b), w in sorted(edges.items(), key=lambda kv: -kv[1]):
        if a in keep and b in keep:
            lines.append(f"    {node_id(a)} --> {node_id(b)}")
    for (a, nid), w in sorted(ext_edges.items(), key=lambda kv: -kv[1]):
        if a in keep:
            lines.append(f"    {node_id(a)} -.-> ext_{nid}")  # ext_ prefix: never collides with a module named db/cache/…
    return "\n".join(lines)


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    root = Path(argv[1])
    depth, max_nodes = 2, 14
    if "--depth" in argv:
        depth = int(argv[argv.index("--depth") + 1])
    if "--max-nodes" in argv:
        max_nodes = int(argv[argv.index("--max-nodes") + 1])
    edges, externals, ext_edges, group_files = build(root, depth)
    go_share = sum(1 for _, r in source_files(root.resolve()) if r.endswith(".go")) / max(1, sum(group_files.values()))
    # Go imports whole packages, so file-level edges would be arbitrary there
    if "--depth" not in argv and ("--files" in argv or (len(group_files) < 4 and go_share < 0.5)):
        # too few packages for a useful picture (single-package repo): switch to file-level nodes
        edges, externals, ext_edges, group_files = build(root, 0)
        print("%% file-level graph (few packages found); pass --depth N to force package grouping")
    if "--json" in argv:
        print(json.dumps({
            "groups": dict(group_files),
            "edges": [{"from": a, "to": b, "imports": w} for (a, b), w in edges.most_common()],
            "externals": {k: v[0] for k, v in externals.items()},
            "external_edges": [{"from": a, "to": b, "imports": w} for (a, b), w in ext_edges.most_common()],
        }, indent=2))
    if "--mermaid" in argv or "--json" not in argv:
        if not group_files:
            print("%% no source files found")
            return 0
        print("```mermaid")
        print(to_mermaid(edges, externals, ext_edges, group_files, max_nodes))
        print("```")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
