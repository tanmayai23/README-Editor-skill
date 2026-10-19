#!/usr/bin/env python3
"""Collect README-relevant facts about a repository and print them as JSON.

Stdlib only. Usage:
    python analyze_repo.py <repo_path> [--compact]

Facts are evidence for the README writer: everything reported here was found
in a file, so commands and env vars can be quoted without guessing.
"""
from __future__ import annotations

import configparser
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

try:  # Python 3.11+
    import tomllib  # type: ignore
except ImportError:  # pragma: no cover
    tomllib = None

IGNORE_DIRS = {
    ".git", "node_modules", ".venv", "venv", "env", "__pycache__", "dist", "build",
    "target", ".next", ".nuxt", "out", "coverage", ".mypy_cache", ".pytest_cache",
    ".tox", ".idea", ".vscode", "vendor", ".gradle", "bin", "obj", ".dart_tool",
    "Pods", ".turbo", ".cache", "site-packages", ".svelte-kit", ".parcel-cache",
}

# Sample code lives here; its env vars, routes and tests are not the project's own.
# Skipped when collecting facts, but still shown in the tree and listed as "example_dirs".
SAMPLE_DIRS = {"demo", "demos", "example", "examples", "sample", "samples", "fixtures", "testdata"}

EXT_LANG = {
    ".py": "Python", ".ipynb": "Jupyter Notebook", ".js": "JavaScript", ".mjs": "JavaScript",
    ".cjs": "JavaScript", ".jsx": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript",
    ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin", ".kts": "Kotlin",
    ".scala": "Scala", ".rb": "Ruby", ".php": "PHP", ".cs": "C#", ".fs": "F#",
    ".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".hpp": "C++", ".c": "C", ".h": "C",
    ".swift": "Swift", ".m": "Objective-C", ".dart": "Dart", ".ex": "Elixir", ".exs": "Elixir",
    ".erl": "Erlang", ".hs": "Haskell", ".lua": "Lua", ".r": "R", ".R": "R", ".jl": "Julia",
    ".sh": "Shell", ".bash": "Shell", ".ps1": "PowerShell", ".vue": "Vue", ".svelte": "Svelte",
    ".astro": "Astro", ".sol": "Solidity", ".zig": "Zig", ".nim": "Nim", ".clj": "Clojure",
    ".html": "HTML", ".css": "CSS", ".scss": "SCSS", ".sql": "SQL", ".tf": "HCL",
    ".gd": "GDScript", ".cu": "CUDA", ".mojo": "Mojo",
}
MARKUP_LANGS = {"HTML", "CSS", "SCSS"}

FRAMEWORK_HINTS = {
    # JS/TS dependency name -> label
    "next": "Next.js", "react": "React", "vue": "Vue", "nuxt": "Nuxt", "svelte": "Svelte",
    "@sveltejs/kit": "SvelteKit", "@angular/core": "Angular", "express": "Express",
    "fastify": "Fastify", "@nestjs/core": "NestJS", "koa": "Koa", "hono": "Hono",
    "electron": "Electron", "react-native": "React Native", "expo": "Expo", "vite": "Vite",
    "astro": "Astro", "remix": "Remix", "@remix-run/react": "Remix", "tailwindcss": "Tailwind CSS",
    "prisma": "Prisma", "@prisma/client": "Prisma", "drizzle-orm": "Drizzle", "mongoose": "Mongoose",
    "typeorm": "TypeORM", "sequelize": "Sequelize", "graphql": "GraphQL", "@trpc/server": "tRPC",
    "socket.io": "Socket.IO", "three": "Three.js", "jest": "Jest", "vitest": "Vitest",
    "playwright": "Playwright", "@playwright/test": "Playwright", "cypress": "Cypress",
    "commander": "Commander (CLI)", "yargs": "yargs (CLI)", "oclif": "oclif (CLI)",
    "@anthropic-ai/sdk": "Anthropic SDK", "openai": "OpenAI SDK", "langchain": "LangChain",
    "discord.js": "discord.js", "@supabase/supabase-js": "Supabase", "firebase": "Firebase",
}
PY_FRAMEWORK_HINTS = {
    "django": "Django", "flask": "Flask", "fastapi": "FastAPI", "starlette": "Starlette",
    "streamlit": "Streamlit", "gradio": "Gradio", "torch": "PyTorch", "tensorflow": "TensorFlow",
    "jax": "JAX", "keras": "Keras", "transformers": "Transformers", "diffusers": "Diffusers",
    "datasets": "HF Datasets", "peft": "PEFT", "scikit-learn": "scikit-learn", "sklearn": "scikit-learn",
    "pandas": "pandas", "polars": "Polars", "numpy": "NumPy", "langchain": "LangChain",
    "llama-index": "LlamaIndex", "anthropic": "Anthropic SDK", "openai": "OpenAI SDK",
    "click": "Click (CLI)", "typer": "Typer (CLI)", "sqlalchemy": "SQLAlchemy", "pydantic": "Pydantic",
    "celery": "Celery", "pytest": "pytest", "lightning": "Lightning", "pytorch-lightning": "Lightning",
    "xgboost": "XGBoost", "lightgbm": "LightGBM", "opencv-python": "OpenCV", "ultralytics": "Ultralytics YOLO",
    "aiohttp": "aiohttp", "scrapy": "Scrapy", "selenium": "Selenium", "playwright": "Playwright",
    "mlflow": "MLflow", "wandb": "Weights & Biases", "vllm": "vLLM", "accelerate": "Accelerate",
}

ENV_PATTERNS = [
    re.compile(r"process\.env\.([A-Z][A-Z0-9_]{2,})"),
    re.compile(r"process\.env\[['\"]([A-Z][A-Z0-9_]{2,})['\"]\]"),
    re.compile(r"import\.meta\.env\.([A-Z][A-Z0-9_]{2,})"),
    re.compile(r"os\.environ(?:\.get)?\(\s*['\"]([A-Z][A-Z0-9_]{2,})['\"]"),
    re.compile(r"os\.environ\[['\"]([A-Z][A-Z0-9_]{2,})['\"]\]"),
    re.compile(r"os\.getenv\(\s*['\"]([A-Z][A-Z0-9_]{2,})['\"]"),
    re.compile(r"os\.Getenv\(\s*\"([A-Z][A-Z0-9_]{2,})\""),
    re.compile(r"env::var\(\s*\"([A-Z][A-Z0-9_]{2,})\""),
    re.compile(r"System\.getenv\(\s*\"([A-Z][A-Z0-9_]{2,})\""),
    re.compile(r"ENV\[['\"]([A-Z][A-Z0-9_]{2,})['\"]\]"),
    re.compile(r"Deno\.env\.get\(\s*['\"]([A-Z][A-Z0-9_]{2,})['\"]"),
]
ENV_IGNORE = {"NODE_ENV", "PATH", "HOME", "PWD", "USER", "CI", "DEBUG", "PORT_", "TERM", "SHELL"}

LICENSE_SIGNATURES = [
    ("MIT", r"Permission is hereby granted, free of charge"),
    ("Apache-2.0", r"Apache License,?\s+Version 2\.0"),
    ("GPL-3.0", r"GNU GENERAL PUBLIC LICENSE\s+Version 3"),
    ("GPL-2.0", r"GNU GENERAL PUBLIC LICENSE\s+Version 2"),
    ("AGPL-3.0", r"GNU AFFERO GENERAL PUBLIC LICENSE"),
    ("LGPL-3.0", r"GNU LESSER GENERAL PUBLIC LICENSE"),
    ("MPL-2.0", r"Mozilla Public License,?\s+(?:Version|v\.)\s*2\.0"),
    ("BSD-3-Clause", r"Neither the name of"),
    ("BSD-2-Clause", r"Redistributions in binary form must reproduce"),
    ("ISC", r"Permission to use, copy, modify, and/or distribute this software for any purpose"),
    ("Unlicense", r"This is free and unencumbered software released into the public domain"),
    ("CC-BY-4.0", r"Creative Commons Attribution 4\.0"),
    ("CC0-1.0", r"CC0 1\.0 Universal"),
]

TEST_NAME = re.compile(r"(_test\.go|\.test\.[jt]sx?|\.spec\.[jt]sx?|^test_.*\.py)$")
CONFIG_PATTERNS = [
    (r"viper\.SetConfigName\([^)]*\)", "viper config file"),
    (r"viper\.AutomaticEnv\(\)", "viper: env vars override config keys"),
    (r"viper\.SetEnvPrefix\([^)]*\)", "viper env prefix"),
    (r"\.PersistentFlags\(\)\.\w+\(\s*\"[\w-]+\"", "cobra persistent flag"),
    (r"class \w+\(BaseSettings\)", "pydantic-settings (env vars map to fields)"),
    (r"env_prefix\s*=\s*['\"][^'\"]+['\"]", "pydantic env prefix"),
    (r"load_dotenv\(", "python-dotenv (.env file)"),
    (r"require\(['\"]dotenv['\"]\)|import ['\"]dotenv/config['\"]", "dotenv (.env file)"),
    (r"@click\.option\(\s*['\"]--[\w-]+", "click option"),
    (r"typer\.Option\(", "typer option"),
    (r"argparse\.ArgumentParser\(", "argparse CLI"),
    (r"#\[derive\([^)]*Parser", "clap derive CLI"),
    (r"\.option\(\s*['\"]-", "commander/yargs option"),
    (r"config\.ya?ml|config\.toml|\.\w+rc\b", "config file reference"),
]
KEEP_DOT_DIRS ={".github", ".gitlab", ".circleci", ".devcontainer", ".husky", ".storybook"}
MAX_FILES = 20000
MAX_SCAN_BYTES = 400_000


def read_text(path: Path, limit: int = MAX_SCAN_BYTES) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read(limit)
    except OSError:
        return ""


def load_json(path: Path):
    try:
        return json.loads(read_text(path, 5_000_000))
    except (ValueError, OSError):
        return None


def load_toml(path: Path):
    if tomllib is None:
        return mini_toml(read_text(path))
    try:
        with open(path, "rb") as fh:
            return tomllib.load(fh)
    except Exception:
        return mini_toml(read_text(path))


def mini_toml(text: str) -> dict:
    """Fallback for Python < 3.11: tables, string/bool/number scalars, and (multi-line) string arrays.
    Enough for [project], [tool.poetry], [package], [workspace], [dependencies] lookups."""
    data: dict = {}
    cur = data
    lines = iter(text.splitlines())
    for raw in lines:
        line = raw.split(" #", 1)[0].strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^\[\[?([^\]]+)\]\]?$", line)
        if m:
            cur = data
            for part in [p.strip().strip('"') for p in m.group(1).split(".")]:
                cur = cur.setdefault(part, {})
            continue
        m = re.match(r'^("?[\w\-.]+"?)\s*=\s*(.*)$', line)
        if not m:
            continue
        key, val = m.group(1).strip('"'), m.group(2).strip()
        if val.startswith("[") and val.count("[") > val.count("]"):
            for more in lines:
                val += " " + more.split(" #", 1)[0].strip()
                if val.count("[") <= val.count("]"):
                    break
        if val.startswith("["):
            cur[key] = re.findall(r'"([^"]*)"|\'([^\']*)\'', val)
            cur[key] = [a or b for a, b in cur[key]]
        elif val.startswith("{"):
            cur[key] = dict(re.findall(r'([\w\-]+)\s*=\s*"([^"]*)"', val))
        elif val[:1] in "\"'":
            cur[key] = val.strip("\"'")
        elif val in ("true", "false"):
            cur[key] = val == "true"
        else:
            cur[key] = val
    return data


def is_sample_dir(root: Path, dirpath: str, d: str) -> bool:
    """demo/, examples/ ... hold sample code, except inside JVM source sets (src/main/java/com/example)."""
    if d.lower() not in SAMPLE_DIRS:
        return False
    parent = os.path.relpath(dirpath, root).replace(os.sep, "/")
    return not re.search(r"(^|/)src/(main|test)(/|$)", parent)


def walk(root: Path):
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not is_sample_dir(root, dirpath, d)
                       and (not d.startswith(".") or d in KEEP_DOT_DIRS)]
        for name in filenames:
            count += 1
            if count > MAX_FILES:
                return
            yield Path(dirpath) / name


def find_example_dirs(root: Path, limit: int = 10):
    found = []
    for dirpath, dirnames, _ in os.walk(root):
        keep = []
        for d in dirnames:
            if is_sample_dir(root, dirpath, d):
                found.append(rel(root, Path(dirpath) / d))
            elif d not in IGNORE_DIRS and not d.startswith("."):
                keep.append(d)
        dirnames[:] = keep
        if len(found) >= limit:
            break
    return sorted(found)[:limit]


def rel(root: Path, p: Path) -> str:
    return p.relative_to(root).as_posix()


def git_remote(root: Path):
    cfg = root / ".git" / "config"
    url = None
    if cfg.exists():
        m = re.search(r'\[remote "origin"\][^\[]*?url\s*=\s*(\S+)', read_text(cfg), re.S)
        if m:
            url = m.group(1)
    if not url:
        try:
            url = subprocess.run(["git", "-C", str(root), "remote", "get-url", "origin"],
                                 capture_output=True, text=True, timeout=5).stdout.strip() or None
        except Exception:
            url = None
    if not url:
        return None
    m = re.search(r"(github\.com|gitlab\.com|bitbucket\.org|huggingface\.co)[:/]([^/]+)/([^/\s]+?)(?:\.git)?/?$", url)
    info = {"url": url}
    if m:
        info.update({"host": m.group(1), "owner": m.group(2), "repo": m.group(3),
                     "web_url": f"https://{m.group(1)}/{m.group(2)}/{m.group(3)}"})
    return info


def default_branch(root: Path):
    head = read_text(root / ".git" / "HEAD")
    m = re.search(r"ref: refs/heads/(\S+)", head)
    return m.group(1) if m else None


def detect_license(root: Path, files):
    for p in files:
        if re.match(r"^(LICEN[SC]E|COPYING)(\.\w+)?$", p.name, re.I) and p.parent == root:
            text = read_text(p, 20000)
            for spdx, sig in LICENSE_SIGNATURES:
                if re.search(sig, text, re.I):
                    return {"file": p.name, "spdx": spdx}
            return {"file": p.name, "spdx": "UNKNOWN"}
    return None


def parse_requirements(text: str):
    deps = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        name = re.split(r"[<>=!~\[; ]", line, maxsplit=1)[0].strip().lower()
        if name:
            deps.append(name)
    return deps


def dep_names(spec_list):
    out = []
    for s in spec_list or []:
        name = re.split(r"[<>=!~\[; (]", str(s), maxsplit=1)[0].strip().lower()
        if name:
            out.append(name)
    return out


def analyze(root: Path) -> dict:
    root = root.resolve()
    files = list(walk(root))
    facts: dict = {"root": str(root), "name": root.name}

    # ---- languages -------------------------------------------------------
    loc = Counter()
    file_count = Counter()
    for p in files:
        lang = EXT_LANG.get(p.suffix)
        if not lang:
            continue
        try:
            size = p.stat().st_size
        except OSError:
            continue
        if size > 2_000_000:
            continue
        file_count[lang] += 1
        loc[lang] += read_text(p, 2_000_000).count("\n") + 1
    total = sum(loc.values()) or 1
    facts["languages"] = [
        {"name": k, "loc": v, "files": file_count[k], "pct": round(100 * v / total, 1)}
        for k, v in loc.most_common(10)
    ]
    code_langs = [l["name"] for l in facts["languages"] if l["name"] not in MARKUP_LANGS]
    facts["primary_language"] = code_langs[0] if code_langs else (facts["languages"][0]["name"] if facts["languages"] else None)

    names = {rel(root, p): p for p in files}
    top = {p.name: p for p in files if p.parent == root}

    manifests = []
    commands: dict = {}
    deps_all: set = set()
    frameworks: set = set()
    bins: dict = {}
    package: dict = {}
    workspaces = []

    # ---- JavaScript / TypeScript -----------------------------------------
    if "package.json" in top:
        pkg = load_json(top["package.json"]) or {}
        manifests.append("package.json")
        package.update({k: pkg.get(k) for k in ("name", "version", "description", "homepage", "license", "author", "keywords", "private") if pkg.get(k) is not None})
        if isinstance(pkg.get("repository"), (str, dict)):
            package["repository"] = pkg["repository"] if isinstance(pkg["repository"], str) else pkg["repository"].get("url")
        if pkg.get("engines"):
            package["engines"] = pkg["engines"]
        pm = "npm"
        if "pnpm-lock.yaml" in top or str(pkg.get("packageManager", "")).startswith("pnpm"):
            pm = "pnpm"
        elif "yarn.lock" in top or str(pkg.get("packageManager", "")).startswith("yarn"):
            pm = "yarn"
        elif "bun.lockb" in top or "bun.lock" in top or str(pkg.get("packageManager", "")).startswith("bun"):
            pm = "bun"
        facts["js_package_manager"] = pm
        run = {"npm": "npm run", "pnpm": "pnpm", "yarn": "yarn", "bun": "bun run"}[pm]
        install = {"npm": "npm install", "pnpm": "pnpm install", "yarn": "yarn", "bun": "bun install"}[pm]
        commands["install"] = install
        scripts = pkg.get("scripts") or {}
        commands["scripts"] = {k: {"run": f"{run} {k}" if k not in ("start", "test") or pm != "npm" else f"npm {k}", "does": v} for k, v in scripts.items()}
        deps = {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {}), **(pkg.get("peerDependencies") or {})}
        deps_all.update(deps.keys())
        for d in deps:
            if d in FRAMEWORK_HINTS:
                frameworks.add(FRAMEWORK_HINTS[d])
        if pkg.get("bin"):
            b = pkg["bin"]
            bins.update({pkg.get("name", "cli"): b} if isinstance(b, str) else b)
        if pkg.get("main") or pkg.get("exports") or pkg.get("module"):
            package["entry"] = pkg.get("main") or pkg.get("module") or "exports"
        if pkg.get("workspaces"):
            ws = pkg["workspaces"]
            workspaces += ws if isinstance(ws, list) else ws.get("packages", [])
        if not pkg.get("private") and pkg.get("name"):
            package["publishable_npm"] = True
        if "typescript" in deps or "tsconfig.json" in top:
            frameworks.add("TypeScript")
    if "pnpm-workspace.yaml" in top:
        workspaces += re.findall(r"-\s*['\"]?([^'\"\n]+)", read_text(top["pnpm-workspace.yaml"]))
    for mono in ("turbo.json", "nx.json", "lerna.json"):
        if mono in top:
            manifests.append(mono)

    # ---- Python ------------------------------------------------------------
    py_deps: list = []
    if "pyproject.toml" in top:
        manifests.append("pyproject.toml")
        data = load_toml(top["pyproject.toml"]) or {}
        proj = data.get("project") or {}
        poetry = (data.get("tool") or {}).get("poetry") or {}
        meta = proj or poetry
        for k in ("name", "version", "description", "requires-python", "license", "keywords"):
            if meta.get(k):
                package.setdefault(k if k != "requires-python" else "requires_python", meta[k] if not isinstance(meta[k], dict) else meta[k].get("text") or meta[k].get("file"))
        py_deps += dep_names(proj.get("dependencies"))
        for grp in (proj.get("optional-dependencies") or {}).values():
            py_deps += dep_names(grp)
        py_deps += [d.lower() for d in (poetry.get("dependencies") or {}) if d.lower() != "python"]
        scripts = proj.get("scripts") or poetry.get("scripts") or {}
        bins.update(scripts)
        tool = data.get("tool") or {}
        build = (data.get("build-system") or {}).get("build-backend", "")
        if "uv.lock" in top or "uv" in tool:
            facts["py_package_manager"] = "uv"
            commands["py_install"] = "uv sync"
        elif poetry or "poetry.lock" in top:
            facts["py_package_manager"] = "poetry"
            commands["py_install"] = "poetry install"
        elif "pdm.lock" in top or "pdm" in tool:
            facts["py_package_manager"] = "pdm"
            commands["py_install"] = "pdm install"
        elif "hatch" in build or "hatch" in tool:
            facts["py_package_manager"] = "hatch"
            commands["py_install"] = 'pip install -e .'
        else:
            facts["py_package_manager"] = "pip"
            commands["py_install"] = 'pip install -e .'
        if proj.get("name") or poetry.get("name"):
            package["publishable_pypi"] = True
            package["pypi_install"] = f"pip install {proj.get('name') or poetry.get('name')}"
        if "pytest" in tool or "pytest" in py_deps:
            commands.setdefault("test", "pytest")
        if "ruff" in tool:
            commands.setdefault("lint", "ruff check .")
    for req in ("requirements.txt", "requirements-dev.txt", "requirements/base.txt", "environment.yml", "Pipfile"):
        p = names.get(req)
        if p:
            manifests.append(req)
            if req.endswith(".txt"):
                py_deps += parse_requirements(read_text(p))
                commands.setdefault("py_install", f"pip install -r {req}")
            elif req == "environment.yml":
                commands.setdefault("py_install", "conda env create -f environment.yml")
            elif req == "Pipfile":
                commands.setdefault("py_install", "pipenv install")
    if "setup.py" in top:
        manifests.append("setup.py")
        txt = read_text(top["setup.py"])
        m = re.search(r"name\s*=\s*['\"]([^'\"]+)", txt)
        if m:
            package.setdefault("name", m.group(1))
        commands.setdefault("py_install", "pip install -e .")
    if "setup.cfg" in top:
        cp = configparser.ConfigParser()
        try:
            cp.read(top["setup.cfg"], encoding="utf-8")
            if cp.has_option("metadata", "name"):
                package.setdefault("name", cp.get("metadata", "name"))
        except configparser.Error:
            pass
    for d in py_deps:
        deps_all.add(d)
        if d in PY_FRAMEWORK_HINTS:
            frameworks.add(PY_FRAMEWORK_HINTS[d])
    if "manage.py" in top:
        frameworks.add("Django")
        commands.setdefault("run", "python manage.py runserver")

    # ---- Other ecosystems ------------------------------------------------
    if "Cargo.toml" in top:
        manifests.append("Cargo.toml")
        data = load_toml(top["Cargo.toml"]) or {}
        pk = data.get("package") or {}
        package.update({k: pk.get(k) for k in ("name", "version", "description", "license", "repository") if pk.get(k)})
        commands.update({"build": "cargo build --release", "test": "cargo test", "run": "cargo run"})
        if pk.get("name"):
            package["cargo_install"] = f"cargo install {pk['name']}" if (data.get("bin") or (root / "src" / "main.rs").exists()) else f"cargo add {pk['name']}"
        if data.get("workspace"):
            workspaces += (data["workspace"].get("members") or [])
        deps_all.update((data.get("dependencies") or {}).keys())
        for d, lbl in (("tokio", "Tokio"), ("axum", "Axum"), ("actix-web", "Actix Web"), ("clap", "clap (CLI)"), ("serde", "Serde"), ("bevy", "Bevy"), ("tauri", "Tauri")):
            if d in (data.get("dependencies") or {}):
                frameworks.add(lbl)
    if "go.mod" in top:
        manifests.append("go.mod")
        txt = read_text(top["go.mod"])
        m = re.search(r"^module\s+(\S+)", txt, re.M)
        gov = re.search(r"^go\s+(\S+)", txt, re.M)
        if m:
            package["go_module"] = m.group(1)
            cmd_dirs = sorted(d.name for d in (root / "cmd").iterdir() if d.is_dir()) if (root / "cmd").is_dir() else []
            if (root / "main.go").exists():
                package["go_install"] = f"go install {m.group(1)}@latest"
            elif cmd_dirs:  # no main package at the module root: install the commands under cmd/
                package["go_install"] = f"go install {m.group(1)}/cmd/{cmd_dirs[0] if len(cmd_dirs) == 1 else '...'}@latest"
            else:
                package["go_install"] = f"go get {m.group(1)}"
        if gov:
            package["go_version"] = gov.group(1)
        commands.update({"build": "go build ./...", "test": "go test ./..."})
        for d, lbl in (("gin-gonic/gin", "Gin"), ("labstack/echo", "Echo"), ("gofiber/fiber", "Fiber"), ("spf13/cobra", "Cobra (CLI)"), ("gorm.io", "GORM"), ("grpc", "gRPC")):
            if d in txt:
                frameworks.add(lbl)
    if "pom.xml" in top:
        manifests.append("pom.xml")
        commands.update({"build": "mvn package", "test": "mvn test"})
        if "spring-boot" in read_text(top["pom.xml"]):
            frameworks.add("Spring Boot")
    for g in ("build.gradle", "build.gradle.kts"):
        if g in top:
            manifests.append(g)
            wrapper = "./gradlew" if "gradlew" in top else "gradle"
            commands.update({"build": f"{wrapper} build", "test": f"{wrapper} test"})
            txt = read_text(top[g])
            if "spring" in txt:
                frameworks.add("Spring Boot")
            if "com.android" in txt:
                frameworks.add("Android")
    if "Gemfile" in top:
        manifests.append("Gemfile")
        commands.setdefault("install", "bundle install")
        if "rails" in read_text(top["Gemfile"]):
            frameworks.add("Ruby on Rails")
    if "composer.json" in top:
        manifests.append("composer.json")
        commands.setdefault("install", "composer install")
        if "laravel" in read_text(top["composer.json"]):
            frameworks.add("Laravel")
    if "pubspec.yaml" in top:
        manifests.append("pubspec.yaml")
        commands.update({"install": "flutter pub get", "run": "flutter run", "test": "flutter test"})
        frameworks.add("Flutter")
    if "mix.exs" in top:
        manifests.append("mix.exs")
        commands.update({"install": "mix deps.get", "test": "mix test"})
        if "phoenix" in read_text(top["mix.exs"]):
            frameworks.add("Phoenix")
            commands.setdefault("run", "mix phx.server")
    csproj = [p for p in files if p.suffix in (".csproj", ".sln")]
    if csproj:
        manifests.append(rel(root, csproj[0]))
        commands.update({"build": "dotnet build", "test": "dotnet test", "run": "dotnet run"})
    if "CMakeLists.txt" in top:
        manifests.append("CMakeLists.txt")
        commands.setdefault("build", "cmake -B build && cmake --build build")
    if "deno.json" in top or "deno.jsonc" in top:
        dj = "deno.json" if "deno.json" in top else "deno.jsonc"
        manifests.append(dj)
        frameworks.add("Deno")
        commands.setdefault("test", "deno test")
        txt = re.sub(r"^\s*//.*$", "", read_text(top[dj]), flags=re.M)
        try:
            tasks = (json.loads(txt) or {}).get("tasks") or {}
        except (ValueError, AttributeError):
            tasks = {}
        if isinstance(tasks, dict):
            scripts = commands.setdefault("scripts", {})
            for k, v in tasks.items():
                scripts.setdefault(k, {"run": f"deno task {k}", "does": v if isinstance(v, str) else (v or {}).get("command")})
    if "Package.swift" in top:
        manifests.append("Package.swift")
        commands.update({"build": "swift build", "test": "swift test", "run": "swift run"})
        if "vapor" in read_text(top["Package.swift"]).lower():
            frameworks.add("Vapor")
    if "build.zig" in top:
        manifests.append("build.zig")
        commands.update({"build": "zig build", "test": "zig build test"})
    cabal = sorted(n for n in top if n.endswith(".cabal"))
    if "stack.yaml" in top:
        manifests.append("stack.yaml")
        manifests += cabal[:1]
        commands.update({"build": "stack build", "test": "stack test"})
    elif cabal:
        manifests.append(cabal[0])
        commands.update({"build": "cabal build", "test": "cabal test"})

    # ---- Make / Just / Task ------------------------------------------------
    for mf in ("Makefile", "makefile", "GNUmakefile"):
        if mf in top:
            targets = re.findall(r"^([a-zA-Z][\w\-.]*):(?!=)", read_text(top[mf]), re.M)
            commands["make_targets"] = sorted(set(t for t in targets if t not in (".PHONY",)))[:40]
    if "justfile" in top or "Justfile" in top:
        jf = top.get("justfile") or top.get("Justfile")
        commands["just_recipes"] = sorted(set(re.findall(r"^([a-zA-Z][\w\-]*)[^:\n]*:(?!=)", read_text(jf), re.M)))[:40]
    if "Taskfile.yml" in top:
        commands["taskfile"] = True

    # ---- Containers / infra ----------------------------------------------
    docker = {}
    if "Dockerfile" in top:
        txt = read_text(top["Dockerfile"])
        docker["dockerfile"] = True
        ports = re.findall(r"^EXPOSE\s+(.+)$", txt, re.M)
        if ports:
            docker["exposed_ports"] = " ".join(ports).split()
        base = re.findall(r"^FROM\s+(\S+)", txt, re.M)
        if base:
            docker["base_images"] = base
    for cf in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"):
        if cf in top:
            txt = read_text(top[cf])
            m = re.search(r"^services:\s*\n((?:[ \t]+.*\n?|\n)+)", txt, re.M)
            svc = []
            if m:
                indent = None
                for line in m.group(1).splitlines():
                    mm = re.match(r"^([ \t]+)([\w\-.]+):\s*$", line)
                    if mm:
                        if indent is None:
                            indent = mm.group(1)
                        if mm.group(1) == indent:
                            svc.append(mm.group(2))
            docker["compose_file"] = cf
            docker["compose_services"] = svc
            docker["compose_up"] = "docker compose up"
    if docker:
        facts["docker"] = docker
    infra = [x for x in ("k8s", "kubernetes", "helm", "charts", "terraform", "infra", "deploy") if (root / x).is_dir()]
    for f in ("vercel.json", "netlify.toml", "fly.toml", "render.yaml", "railway.json", "app.yaml", "Procfile", "serverless.yml", "wrangler.toml", "firebase.json", "amplify.yml"):
        if f in top:
            infra.append(f)
    if infra:
        facts["deploy_hints"] = infra

    # ---- CI ------------------------------------------------------------------
    ci = []
    wf_dir = root / ".github" / "workflows"
    if wf_dir.is_dir():
        for wf in sorted(wf_dir.glob("*.y*ml")):
            txt = read_text(wf, 50000)
            m = re.search(r"^name:\s*['\"]?(.+?)['\"]?\s*$", txt, re.M)
            ci.append({"provider": "github-actions", "file": rel(root, wf), "name": m.group(1) if m else wf.stem})
    for f, prov in ((".gitlab-ci.yml", "gitlab-ci"), (".circleci/config.yml", "circleci"), (".travis.yml", "travis"), ("azure-pipelines.yml", "azure-pipelines"), ("Jenkinsfile", "jenkins"), ("bitbucket-pipelines.yml", "bitbucket")):
        if f in names:
            ci.append({"provider": prov, "file": f})
    facts["ci"] = ci
    facts["coverage_service"] = next((s for s in ("codecov", "coveralls") if any(s in read_text(root / c["file"], 50000).lower() for c in ci if c["provider"] == "github-actions") or (root / f".{s}.yml").exists() or (root / f"{s}.yml").exists()), None)

    # ---- Env vars --------------------------------------------------------
    env = {}
    for ef in (".env.example", ".env.sample", ".env.template", ".env.dist", "example.env", ".env.local.example"):
        p = names.get(ef)
        if p:
            for line in read_text(p).splitlines():
                m = re.match(r"^\s*(?:export\s+)?([A-Z][A-Z0-9_]*)\s*=\s*(.*)$", line)
                if m:
                    env[m.group(1)] = {"source": ef, "example": m.group(2).strip().strip('"\'')[:80]}
    code_ext = {".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".go", ".rs", ".java", ".kt", ".rb"}
    for p in files:
        if p.suffix not in code_ext or "test" in p.name.lower():
            continue
        txt = read_text(p, 200_000)
        for pat in ENV_PATTERNS:
            for var in pat.findall(txt):
                if var not in ENV_IGNORE and var not in env:
                    env[var] = {"source": rel(root, p)}
    facts["env_vars"] = env

    # ---- Entry points ----------------------------------------------------
    entry_candidates = [
        "main.py", "app.py", "__main__.py", "cli.py", "server.py", "manage.py", "train.py", "inference.py",
        "index.js", "index.ts", "main.ts", "main.js", "server.js", "server.ts", "app.js", "app.ts",
        "src/index.ts", "src/index.js", "src/main.ts", "src/main.tsx", "src/main.js", "src/App.tsx", "src/app.ts",
        "src/main.rs", "src/lib.rs", "main.go", "cmd", "src/main/java", "lib/main.dart", "Program.cs",
        "app/page.tsx", "pages/index.tsx", "src/app/page.tsx", "app/layout.tsx",
    ]
    facts["entrypoints"] = [e for e in entry_candidates if (root / e).exists()]
    if (root / "cmd").is_dir():
        facts["go_cmds"] = sorted(d.name for d in (root / "cmd").iterdir()
                                  if d.is_dir() and d.name not in ("testdata", "internal") and any(d.glob("*.go")))
    if package.get("go_module"):
        mod_name = package["go_module"].rstrip("/").split("/")[-1]
        if re.fullmatch(r"v\d+", mod_name):  # github.com/x/y/v2 → y
            mod_name = package["go_module"].rstrip("/").split("/")[-2]
        if (root / "main.go").exists() and "package main" in read_text(root / "main.go", 4000):
            bins.setdefault(mod_name, ".")
        for c in facts.get("go_cmds", []):
            if "package main" in "".join(read_text(f, 2000) for f in (root / "cmd" / c).glob("*.go")):
                bins.setdefault(c, f"./cmd/{c}")
    facts["bins"] = bins

    # ---- HTTP routes (light heuristic) -------------------------------------
    routes = []
    route_pats = [
        re.compile(r"@(?:app|router|bp|api)\.(get|post|put|patch|delete)\(\s*['\"]([^'\"]+)"),
        re.compile(r"\b(?:app|router)\.(get|post|put|patch|delete)\(\s*['\"`]([^'\"`]+)"),
        re.compile(r"@(Get|Post|Put|Patch|Delete)Mapping\(\s*(?:value\s*=\s*)?\"([^\"]+)"),
        re.compile(r"\.(GET|POST|PUT|PATCH|DELETE)\(\s*\"([^\"]+)"),
        re.compile(r"path\(\s*['\"]([^'\"]*)['\"]"),
    ]
    for p in files:
        if p.suffix not in code_ext or len(routes) >= 60:
            continue
        txt = read_text(p, 200_000)
        for pat in route_pats:
            for m in pat.findall(txt):
                method, path = (m if isinstance(m, tuple) else ("ANY", m))
                routes.append({"method": method.upper(), "path": path or "/", "file": rel(root, p)})
    facts["http_routes"] = routes[:60]

    # ---- Tests / docs / misc -----------------------------------------------
    facts["example_dirs"] = find_example_dirs(root)
    facts["tests"] = sorted({rel(root, p).split("/")[0] for p in files if re.search(r"(^|/)(tests?|__tests__|spec)(/|$)", rel(root, p)) or re.search(r"(_test\.go|\.test\.[jt]sx?|\.spec\.[jt]sx?|^test_.*\.py)$", p.name)})[:10]
    facts["docs"] = {
        "dirs": [d for d in ("docs", "doc", "documentation", "website", "examples", "example", "notebooks", "samples") if (root / d).is_dir()],
        "mkdocs": "mkdocs.yml" in top, "docusaurus": any(n.startswith("docusaurus.config") for n in top),
        "sphinx": (root / "docs" / "conf.py").exists(), "storybook": (root / ".storybook").is_dir(),
    }
    facts["community_files"] = {f: (f in names or f".github/{f}" in names or f"docs/{f}" in names) for f in (
        "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md", "SUPPORT.md", "CHANGELOG.md", "CITATION.cff",
        "FUNDING.yml", "pull_request_template.md")}
    facts["community_files"]["ISSUE_TEMPLATE"] = (root / ".github" / "ISSUE_TEMPLATE").is_dir()

    readmes = [rel(root, p) for p in files if p.parent == root and re.match(r"^readme(\.\w+)?$", p.name, re.I)]
    facts["existing_readme"] = readmes[0] if readmes else None
    if readmes:
        facts["existing_readme_lines"] = read_text(root / readmes[0]).count("\n")
    facts["images"] = sorted(rel(root, p) for p in files if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp") and re.search(r"(logo|banner|screenshot|demo|preview|hero|social|architecture|diagram)", p.name, re.I))[:25]

    # ---- Hugging Face artifacts -------------------------------------------
    hf = {}
    weight_files = [rel(root, p) for p in files if p.suffix in (".safetensors", ".bin", ".gguf", ".pt", ".pth", ".onnx", ".h5", ".ckpt") and p.stat().st_size > 0]
    if weight_files:
        hf["weights"] = weight_files[:10]
    if "config.json" in top:
        cfg = load_json(top["config.json"]) or {}
        if isinstance(cfg, dict) and (cfg.get("architectures") or cfg.get("model_type")):
            hf["model_config"] = {k: cfg.get(k) for k in ("architectures", "model_type", "hidden_size", "num_hidden_layers", "vocab_size", "torch_dtype") if cfg.get(k) is not None}
    if "adapter_config.json" in top:
        ac = load_json(top["adapter_config.json"]) or {}
        hf["adapter"] = {k: ac.get(k) for k in ("base_model_name_or_path", "peft_type", "r", "task_type") if ac.get(k) is not None}
    if "tokenizer_config.json" in top:
        hf["tokenizer"] = True
    data_files = [rel(root, p) for p in files if p.suffix in (".parquet", ".arrow", ".jsonl", ".csv", ".tsv") and "node_modules" not in str(p)]
    if data_files:
        hf["data_files"] = data_files[:15]
    if readmes:
        head = read_text(root / readmes[0], 4000)
        if head.startswith("---"):
            hf["existing_frontmatter"] = head.split("---", 2)[1].strip()[:1500] if head.count("---") >= 2 else None
    for f in ("app.py", "streamlit_app.py"):
        if f in top:
            txt = read_text(top[f])
            if "gradio" in txt:
                hf["space_sdk_guess"] = "gradio"
            elif "streamlit" in txt:
                hf["space_sdk_guess"] = "streamlit"
    if hf:
        facts["huggingface"] = hf

    # ---- Monorepo ----------------------------------------------------------
    pkgs = []
    for pattern in workspaces:
        base = pattern.rstrip("/*").rstrip("/**")
        d = root / base
        if d.is_dir():
            if pattern.endswith("*"):
                pkgs += [rel(root, c) for c in sorted(d.iterdir()) if c.is_dir() and not c.name.startswith(".")]
            else:
                pkgs.append(base)
    for d in ("packages", "apps", "services", "libs", "crates", "modules"):
        if (root / d).is_dir() and not any(p.startswith(d + "/") for p in pkgs):
            sub = [rel(root, c) for c in sorted((root / d).iterdir()) if c.is_dir() and any((c / m).exists() for m in ("package.json", "pyproject.toml", "Cargo.toml", "go.mod", "setup.py"))]
            pkgs += sub
    for d in ("backend", "frontend", "server", "client", "api", "web", "app", "worker", "mobile", "docs", "website"):
        c = root / d
        if c.is_dir() and d not in pkgs and any((c / m).exists() for m in ("package.json", "pyproject.toml", "requirements.txt", "Cargo.toml", "go.mod", "pubspec.yaml")):
            pkgs.append(d)
    if pkgs:
        facts["monorepo_packages"] = pkgs[:40]
        details = []
        for sp in pkgs[:20]:
            info = subpackage_info(root / sp)
            if info:
                info["path"] = sp
                details.append(info)
                frameworks.update(info.get("frameworks", []))
        facts["packages_detail"] = details

    # ---- Tree & key files ----------------------------------------------------
    facts["tree"] = make_tree(root, max_depth=2, max_entries=60)
    key = []
    if facts.get("existing_readme"):
        key.append(facts["existing_readme"])
    key += [m for m in manifests if m in names]
    key += [e for e in facts["entrypoints"] if (root / e).is_file()][:4]
    if docker.get("dockerfile"):
        key.append("Dockerfile")
    if docker.get("compose_file"):
        key.append(docker["compose_file"])
    key += [c["file"] for c in ci[:2]]
    # files that usually define the CLI surface / app wiring
    for cand in ("cmd/root.go", "cmd/main.go", "src/cli.py", "cli.py", "src/cli.ts", "src/cli.js", "src/main.rs",
                 "src/app.ts", "app/main.py", "backend/app/main.py", "src/routes", "prisma/schema.prisma"):
        if (root / cand).exists():
            key.append(cand)
    key += [b.lstrip("./") for b in bins.values() if isinstance(b, str) and (root / b).is_file()]
    facts["key_files"] = list(dict.fromkeys(k for k in key if k))[:14]

    # config systems: tell the writer where settings come from beyond plain env vars
    hints = []
    for p in files:
        if p.suffix not in (".go", ".py", ".ts", ".js", ".rs") or TEST_NAME.search(p.name):
            continue
        txt = read_text(p, 100_000)
        r_ = rel(root, p)
        for pat, label in CONFIG_PATTERNS:
            m = re.search(pat, txt)
            if m:
                hints.append({"file": r_, "kind": label, "match": m.group(0)[:80]})
        if len(hints) > 25:
            break
    if hints:
        facts["config_hints"] = hints

    facts["manifests"] = manifests
    facts["package"] = package
    facts["frameworks"] = sorted(frameworks)
    facts["commands"] = commands
    facts["dependency_count"] = len(deps_all)
    facts["license"] = detect_license(root, files)
    facts["git"] = git_remote(root)
    facts["default_branch"] = default_branch(root)
    facts["project_type_guess"] = guess_type(facts)
    return facts


def subpackage_info(d: Path) -> dict:
    """Light manifest read for a workspace package / sub-project."""
    info: dict = {"frameworks": []}
    fw = set()
    if (d / "package.json").exists():
        pkg = load_json(d / "package.json") or {}
        info["manifest"] = "package.json"
        info["name"] = pkg.get("name")
        info["scripts"] = sorted((pkg.get("scripts") or {}).keys())[:20]
        deps = {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {})}
        fw.update(FRAMEWORK_HINTS[x] for x in deps if x in FRAMEWORK_HINTS)
        if "typescript" in deps:
            fw.add("TypeScript")
    py = []
    if (d / "pyproject.toml").exists():
        data = load_toml(d / "pyproject.toml") or {}
        proj = data.get("project") or {}
        poetry = (data.get("tool") or {}).get("poetry") or {}
        info.setdefault("manifest", "pyproject.toml")
        info.setdefault("name", proj.get("name") or poetry.get("name"))
        py += dep_names(proj.get("dependencies")) + [x.lower() for x in (poetry.get("dependencies") or {})]
        if (d / "uv.lock").exists():
            info["py_install"] = "uv sync"
    if (d / "requirements.txt").exists():
        info.setdefault("manifest", "requirements.txt")
        py += parse_requirements(read_text(d / "requirements.txt"))
    fw.update(PY_FRAMEWORK_HINTS[x] for x in py if x in PY_FRAMEWORK_HINTS)
    if (d / "Cargo.toml").exists():
        info.setdefault("manifest", "Cargo.toml")
    if (d / "go.mod").exists():
        info.setdefault("manifest", "go.mod")
    if (d / "pubspec.yaml").exists():
        info.setdefault("manifest", "pubspec.yaml")
        fw.add("Flutter")
    if (d / "Dockerfile").exists():
        info["dockerfile"] = True
    info["frameworks"] = sorted(fw)
    return info if info.get("manifest") else {}


def make_tree(root: Path, max_depth=2, max_entries=60):
    lines = [root.name + "/"]
    count = 0

    def rec(d: Path, prefix: str, depth: int):
        nonlocal count
        try:
            entries = sorted([e for e in d.iterdir() if e.name not in IGNORE_DIRS and (not e.name.startswith(".") or e.name in (".github",))],
                             key=lambda e: (not e.is_dir(), e.name.lower()))
        except OSError:
            return
        for i, e in enumerate(entries):
            if count >= max_entries:
                lines.append(prefix + "└── …")
                return
            last = i == len(entries) - 1
            lines.append(prefix + ("└── " if last else "├── ") + e.name + ("/" if e.is_dir() else ""))
            count += 1
            if e.is_dir() and depth < max_depth:
                rec(e, prefix + ("    " if last else "│   "), depth + 1)

    rec(root, "", 1)
    return "\n".join(lines)


def guess_type(f: dict) -> str:
    fw = set(f["frameworks"])
    hf = f.get("huggingface") or {}
    if hf.get("model_config") or hf.get("adapter") or (hf.get("weights") and not f["manifests"]):
        return "hf-model"
    if hf.get("space_sdk_guess") and not f.get("package", {}).get("publishable_pypi"):
        return "hf-space-or-demo"
    if f.get("monorepo_packages") and len(f["monorepo_packages"]) > 1:
        return "monorepo"
    if fw & {"PyTorch", "TensorFlow", "JAX", "Transformers", "scikit-learn", "Keras", "Lightning", "Diffusers"}:
        return "ml-project"
    cli_fw = {"Commander (CLI)", "yargs (CLI)", "oclif (CLI)", "Click (CLI)", "Typer (CLI)", "clap (CLI)", "Cobra (CLI)"}
    server_fw = {"Express", "Fastify", "NestJS", "FastAPI", "Flask", "Gin", "Echo", "Fiber", "Axum", "Actix Web", "Spring Boot", "Hono", "Koa", "Phoenix", "Vapor"}
    if fw & cli_fw or (f["bins"] and not fw & server_fw and not f["http_routes"]):
        return "cli"
    if fw & {"Next.js", "React", "Vue", "Nuxt", "Svelte", "SvelteKit", "Angular", "Astro", "Remix", "Ruby on Rails", "Laravel", "Django", "Streamlit", "Gradio", "Flutter", "React Native", "Expo", "Electron", "Tauri"}:
        return "webapp" if not fw & {"Flutter", "React Native", "Expo"} else "mobile"
    if f["http_routes"] or fw & server_fw:
        return "api"
    if f["package"].get("publishable_npm") or f["package"].get("publishable_pypi") or any(
            m in ("Cargo.toml", "go.mod", "Package.swift", "build.zig", "stack.yaml") or m.endswith(".cabal") for m in f["manifests"]):
        return "library"
    if f.get("deploy_hints") and any(h in ("terraform", "k8s", "helm") for h in f["deploy_hints"]):
        return "infra"
    if (f["languages"] and f["languages"][0]["name"] == "Jupyter Notebook"):
        return "research-notebooks"
    return "unknown"


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    root = Path(argv[1])
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    facts = analyze(root)
    indent = None if "--compact" in argv else 2
    print(json.dumps(facts, indent=indent, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
