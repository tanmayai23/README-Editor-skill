#!/usr/bin/env python3
"""Check every command, env var and path a README claims against the repository.

Stdlib only. Usage:
    python verify_readme.py README.md [--repo PATH] [--json] [--min-accuracy N]

Options:
    --repo PATH         repository to check against (default: the README's folder)
    --json              machine-readable output (fixed contract, see below)
    --min-accuracy N    exit 1 if accuracy (percent) < N. A README with no checkable
                        claims passes. Exit 2 on bad input.

Every claim gets one status:
    verified      found in the repo (evidence says where)
    not_found     the repo contradicts it: missing file, script, target, flag, env var...
    unverifiable  cannot be decided offline (third-party tool, placeholder, build output)
    generic       needs nothing from the repo (git status, cd .., echo, brew install...)
accuracy = verified / (verified + not_found); unverifiable and generic are left out.
When a rule is unsure it answers "unverifiable", never "not_found".

JSON: {"readme", "repo", "summary": {verified, not_found, unverifiable, generic, checked,
accuracy}, "by_kind": {kind: {verified, not_found, unverifiable}}, "claims": [{kind, text,
line, status, evidence}]}. Kinds: command, script, flag, env_var, path, package_manager.

What is extracted (HTML comments, including <!-- TODO --> lines, are ignored):
  Commands  Fenced blocks tagged bash/sh/shell/zsh/fish/console/powershell/ps1/pwsh/cmd:
            every line. Untagged/text/terminal blocks: only lines that start with a
            known tool. Prompts ($ , > , PS> , user@host$ ) are stripped; when a block
            has prompts, lines without one are output and skipped. Tree listings
            (├── └──) are skipped. `\\`/backtick continuations are joined, statements
            are split on && || ; & and only the first stage of a | pipe is kept.
            Inline code spans count when they start with a known tool and have 2+ words.
            Each block starts in the README's folder; `cd` is followed within a block.
  Env vars  ALL_CAPS names with an underscore (single words such as PORT only in env
            contexts) found as VAR= / export VAR / set VAR / $env:VAR / ${VAR} / $VAR /
            %VAR% / process.env.VAR in code blocks; inline code in a table whose header
            has "variable", "env" or "name"+"default"; inline code under a heading
            containing "config" or "environment". One claim per name.
  Paths     Relative markdown link/image targets, <img src>, <source srcset>, <a href>
            and reference definitions; inline code that looks like a repo path.

How claims are checked:
  npm/pnpm/yarn/bun     `run X`, `test`, `start`, `yarn X`, `pnpm X`, `bun X` -> script X in
                        any package.json (kind script). Bare install -> a package.json exists.
                        The package manager of dev commands (install/run) must match the
                        lockfile(s) or packageManager field (kind package_manager).
                        `npm install NAME` -> NAME is the project or a dependency, else
                        unverifiable. npx/pnpm dlx/bunx/yarn dlx X -> X is a dependency or
                        bin, else unverifiable. Other npm subcommands are generic.
  Python                `pip install -r F` -> F exists; `pip install [-e] .` -> pyproject.toml/
                        setup.py/setup.cfg; `pip install NAME` -> own package or a listed
                        dependency, else unverifiable. uv sync/poetry/pdm/hatch -> pyproject;
                        pipenv -> Pipfile; conda env create -f F -> F. `uv run`/`poetry run`/
                        `pipenv run`/`pdm run` check the inner command. `python FILE` -> file
                        exists; `python -m mod` -> mod.py, mod/__main__.py (also under src/),
                        or a dependency; stdlib/tool modules are generic, unknown ones
                        unverifiable. uvicorn/gunicorn `mod:app` and `streamlit run F` too.
  make/just/task/deno   Makefile target / justfile recipe / Taskfile task / deno.json task.
                        Pattern rules, includes or $(VAR) targets make a miss unverifiable.
  Other ecosystems      cargo (Cargo.toml; --bin/--example/-p/--features must exist), go
                        (go.mod; package paths must exist), mvn/mvnw, gradle/gradlew, dotnet,
                        flutter/dart, mix, bundle/rails/rake, composer/php artisan, swift,
                        zig, stack/cabal, cmake, meson, pre-commit, tox, nox, terraform:
                        the matching manifest or wrapper exists.
  Docker                compose up/run/... -> compose file (or -f file) exists and every named
                        service is defined; docker build -> Dockerfile (or -f file) and context.
                        docker run is unverifiable unless the image was built above.
  Files                 cd DIR, cp/mv SRC, ./script, bash/sh/pwsh FILE, node/ts-node/tsx/bun/
                        deno run FILE -> the path exists (relative to the current block dir,
                        the README folder or the repo root). After `git clone URL [dir]` the
                        clone folder maps to the repo root; `cd ..`, ~ and absolute paths are
                        generic. Paths under dist/, build/, target/, node_modules/... are build
                        output (unverifiable). A missing path that an earlier command created
                        (mkdir, a scaffolder, another clone) is unverifiable.
  Flags                 For declared bins (pyproject/package.json/Cargo/go cmd), repo scripts
                        run with python/node/./x, python -m <repo module>, cargo run -- and
                        go run: one claim per --long-flag. Verified if the literal --flag is in
                        a source file, or "flag" is quoted (cobra/yargs/flag pkg), or the
                        snake_case name is a field in Rust (clap) or Python using typer.
                        --no-X passes when --X exists. --help/--version are generic; short
                        flags are ignored.
  git clone URL         verified when URL matches the origin remote (https/ssh/.git ignored).
  Env vars              verified if the name is in any non-Markdown text file of the repo
                        (code, .env*, compose, Dockerfile, CI yaml, configs), or is the field
                        of a pydantic BaseSettings/clap env/viper class, or is read implicitly
                        by an SDK the project depends on (OPENAI_API_KEY with openai, ...).
                        Shell/platform variables (PATH, HOME, NODE_ENV, GITHUB_*) are generic.
  Paths                 Links resolve from the README folder (/x from the repo root) and must
                        exist with exact case. Inline paths may also resolve from the repo root
                        or match a repo file by suffix; a bare file name may be anywhere in the
                        repo (else unverifiable). An inline path whose first folder is unknown
                        and not a usual source folder (src, docs, ...) is unverifiable.
                        URLs, anchors, mailto:, GitHub routes (../../issues) and placeholders
                        (<x>, {x}, your-, path/to) are skipped.
  Anything else         an unknown program is unverifiable.
"""
from __future__ import annotations

import json
import os
import posixpath
import re
import shlex
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).parent))
from analyze_repo import IGNORE_DIRS, ENV_PATTERNS, analyze, dep_names, load_json, load_toml, parse_requirements, read_text  # noqa: E402

STATUSES = ("verified", "not_found", "unverifiable", "generic")
KINDS = ("command", "script", "flag", "env_var", "path", "package_manager")
SYMBOL = {"verified": "✓", "not_found": "✗", "unverifiable": "?", "generic": "·"}

# --------------------------------------------------------------------------- vocabulary
STRICT_LANGS = {"bash", "sh", "shell", "zsh", "fish", "console", "powershell", "ps1", "pwsh", "ps", "cmd",
                "bat", "batch", "shell-session", "shellsession", "sh-session", "bash-session", "shellscript"}
LOOSE_LANGS = {"", "text", "txt", "plain", "plaintext", "terminal"}
PS_LANGS = {"powershell", "ps1", "pwsh", "ps", "cmd", "bat", "batch"}
SKIP_DIRS = (set(IGNORE_DIRS) - {"bin"}) | {".hg", ".svn"}
BUILD_DIRS = {"dist", "build", "target", "out", "node_modules", ".venv", "venv", "__pycache__", ".next", ".nuxt",
              "coverage", "obj", "_build", "site", "public/build", ".svelte-kit", "lib-cov", "release"}
COMMON_DIRS = {"src", "lib", "docs", "doc", "app", "apps", "test", "tests", "spec", "scripts", "script", "config",
               "configs", "packages", "cmd", "internal", "pkg", "examples", "example", "public", "assets", "static",
               "templates", "tools", "bin", "server", "client", "api", "web", "frontend", "backend", "data", "notebooks",
               "benchmarks", "migrations", "deploy", "infra", "charts", "k8s", ".github", "crates", "include"}
SOURCE_EXT = {".py", ".pyi", ".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".mts", ".cts", ".go", ".rs", ".java", ".kt",
              ".kts", ".scala", ".rb", ".php", ".cs", ".fs", ".cpp", ".cc", ".cxx", ".hpp", ".c", ".h", ".swift", ".m",
              ".dart", ".ex", ".exs", ".erl", ".hs", ".lua", ".r", ".jl", ".sh", ".bash", ".zsh", ".fish", ".ps1", ".psm1",
              ".bat", ".cmd", ".vue", ".svelte", ".astro", ".zig", ".nim", ".clj", ".groovy", ".pl", ".gd", ".mojo"}
BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".bmp", ".tiff", ".psd", ".mp4", ".mov", ".webm", ".avi",
              ".mp3", ".wav", ".ogg", ".flac", ".zip", ".gz", ".tgz", ".bz2", ".xz", ".7z", ".rar", ".jar", ".war", ".whl",
              ".pdf", ".woff", ".woff2", ".ttf", ".otf", ".eot", ".exe", ".dll", ".so", ".dylib", ".a", ".o", ".pyc",
              ".class", ".bin", ".safetensors", ".pt", ".pth", ".onnx", ".h5", ".ckpt", ".gguf", ".parquet", ".arrow",
              ".npy", ".npz", ".pkl", ".db", ".sqlite", ".lockb", ".wasm", ".mp4", ".pyd"}
MD_EXT = {".md", ".mdx", ".markdown", ".mdown"}
PATH_EXT = {".py", ".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".kt", ".rb", ".php", ".cs",
            ".swift", ".c", ".h", ".cpp", ".hpp", ".sh", ".bash", ".ps1", ".bat", ".json", ".jsonc", ".yaml", ".yml",
            ".toml", ".ini", ".cfg", ".conf", ".env", ".lock", ".md", ".mdx", ".txt", ".sql", ".html", ".css", ".scss",
            ".vue", ".svelte", ".xml", ".gradle", ".cabal", ".nix", ".tf", ".proto", ".graphql", ".prisma", ".ipynb",
            ".csv", ".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".dart", ".ex", ".exs", ".lua", ".zig", ".astro"}
PATH_NAMES = {"Dockerfile", "Makefile", "Procfile", "Gemfile", "Rakefile", "Justfile", "justfile", "Taskfile.yml",
              "Pipfile", "LICENSE", ".env.example", ".gitignore", ".dockerignore", "CODEOWNERS", "Vagrantfile"}

JS_PMS = {"npm", "pnpm", "yarn", "bun"}
LOCKFILES = {"package-lock.json": "npm", "npm-shrinkwrap.json": "npm", "pnpm-lock.yaml": "pnpm",
             "yarn.lock": "yarn", "bun.lockb": "bun", "bun.lock": "bun"}
NPM_BUILTIN = {"install", "i", "ci", "add", "uninstall", "remove", "rm", "un", "update", "up", "upgrade", "run",
               "run-script", "test", "t", "start", "stop", "restart", "publish", "pack", "link", "ln", "unlink", "init",
               "create", "exec", "x", "dlx", "audit", "outdated", "ls", "list", "version", "login", "logout", "config",
               "set", "get", "cache", "help", "view", "info", "show", "doctor", "prune", "dedupe", "rebuild", "explain",
               "why", "fund", "whoami", "global", "store", "setup", "env", "import", "patch", "patch-commit", "root",
               "bin", "licenses", "deploy", "recursive", "workspace", "workspaces", "plugin", "constraints", "dlx",
               "node", "npm", "search", "stage", "unplug", "upgrade-interactive", "pm", "repl", "build", "completion",
               "owner", "access", "team", "token", "profile", "ping", "hook", "star", "stars", "sbom", "query", "diff",
               "shrinkwrap", "edit", "explore", "docs", "bugs", "repo", "pkg", "org", "dist-tag", "deprecate", "s", "se"}
NPM_VALUE_OPTS = {"--filter", "-F", "--workspace", "--prefix", "-C", "--cwd", "--dir", "--registry", "--loglevel",
                  "--tag", "--reporter"}
PY_TOOL_MODULES = {"pip", "venv", "virtualenv", "pytest", "unittest", "doctest", "build", "twine", "black", "ruff",
                   "mypy", "flake8", "isort", "pylint", "coverage", "tox", "nox", "pdb", "cProfile", "profile",
                   "timeit", "ensurepip", "pydoc", "webbrowser", "zipapp", "site", "http.server", "json.tool",
                   "pipx", "uv", "poetry", "jupyter", "notebook", "jupyterlab", "ipykernel", "pre_commit",
                   "compileall", "py_compile", "tabnanny", "trace", "pstats", "sysconfig", "pip_audit", "wheel",
                   "setuptools", "sphinx", "mkdocs", "bandit", "pyright", "hatch", "pdm", "maturin"}
PY_STDLIB = set(getattr(sys, "stdlib_module_names", ())) | {
    "os", "sys", "json", "http", "venv", "unittest", "doctest", "pdb", "timeit", "zipfile", "tarfile", "asyncio",
    "sqlite3", "ast", "dis", "tokenize", "calendar", "base64", "gzip", "uuid", "smtpd", "pydoc", "idlelib", "turtle",
    "this", "antigravity", "platform", "locale", "encodings", "lib2to3", "ensurepip", "compileall", "py_compile",
    "pickletools", "pstats", "profile", "cProfile", "trace", "webbrowser", "zipapp", "mimetypes", "filecmp", "tabnanny"}
GENERIC_PROGRAMS = {
    "echo", "printf", "curl", "wget", "export", "set", "setx", "unset", "source", ".", "mkdir", "md", "ls", "dir", "cat",
    "type", "less", "more", "head", "tail", "open", "xdg-open", "start", "brew", "apt", "apt-get", "yum", "dnf",
    "pacman", "apk", "snap", "choco", "winget", "scoop", "port", "nvm", "fnm", "volta", "pyenv", "rbenv", "rustup",
    "asdf", "mise", "corepack", "sdk", "chmod", "chown", "touch", "rm", "del", "rmdir", "rd", "ssh", "ssh-keygen", "scp",
    "code", "cursor", "vim", "vi", "nano", "emacs", "exit", "clear", "cls", "which", "where", "whoami", "sleep",
    "deactivate", "activate", "history", "alias", "grep", "find", "sed", "awk", "tar", "unzip", "zip", "gpg", "openssl",
    "jq", "yq", "kill", "pkill", "ps", "top", "htop", "xcode-select", "set-executionpolicy", "invoke-webrequest", "iwr",
    "irm", "iex", "write-host", "write-output", "ping", "nc", "telnet", "pwd", "env", "printenv", "date", "true",
    "false", "test", "watch", "xargs", "tee", "sort", "uniq", "wc", "diff", "patch", "ln", "readlink", "realpath",
    "basename", "dirname", "gem", "go-task", "n", "conda-activate", "sha256sum", "shasum", "md5sum", "base64",
    "new-item", "remove-item", "get-content", "get-childitem", "systemctl", "service", "launchctl", "lsof", "netstat",
    "http", "https", "httpie", "xh", "ab", "hey", "wrk", "ngrok", "gh", "hub", "nproc", "ulimit", "trap", "wait",
    "read", "eval", "let", "declare", "local", "if", "then", "else", "fi", "for", "do", "done", "while", "case", "esac",
    "function", "return", "shift", "exec", "ollama", "cloudflared", "openssl", "rsync", "scp", "dig", "nslookup"}
KNOWN_TOOLS = {
    "npm", "pnpm", "yarn", "bun", "bunx", "npx", "pip", "pipx", "uv", "uvx", "poetry", "pdm", "pipenv", "hatch",
    "conda", "mamba", "micromamba", "python", "make", "just", "task", "cargo", "go", "mvn", "./mvnw", "mvnw", "gradle",
    "./gradlew", "gradlew", "dotnet", "flutter", "dart", "mix", "bundle", "rails", "rake", "composer", "php", "swift",
    "zig", "stack", "cabal", "deno", "docker", "docker-compose", "podman", "git", "cd", "node", "ts-node", "tsx",
    "pytest", "tox", "nox", "pre-commit", "uvicorn", "gunicorn", "hypercorn", "streamlit", "fastapi", "kubectl",
    "helm", "cmake", "meson", "terraform", "cp", "mv", "bash", "sh", "zsh", "pwsh", "powershell", "pushd",
    "set-location", "copy", "copy-item", "move", "move-item", "bin/rails", "bin/dev", "ruff", "black", "mypy",
    "flake8", "eslint", "prettier", "tsc", "jest", "vitest", "playwright", "cypress", "next", "vite", "nodemon"}
INLINE_TOOLS = KNOWN_TOOLS - {"cp", "mv", "copy", "move", "task", "next", "bash", "sh", "zsh", "set-location",
                              "copy-item", "move-item", "pushd"}
DEV_TOOLS = {"ruff": ["ruff"], "black": ["black"], "mypy": ["mypy"], "flake8": ["flake8"], "isort": ["isort"],
             "pylint": ["pylint"], "coverage": ["coverage"], "eslint": ["eslint"], "prettier": ["prettier"],
             "tsc": ["typescript"], "jest": ["jest"], "vitest": ["vitest"], "playwright": ["playwright", "@playwright/test"],
             "cypress": ["cypress"], "next": ["next"], "vite": ["vite"], "nodemon": ["nodemon"], "biome": ["@biomejs/biome"]}
NPX_BINS = {"tsc": "typescript", "playwright": "@playwright/test", "nuxi": "nuxt", "ng": "@angular/cli",
            "nest": "@nestjs/cli", "sb": "storybook", "drizzle-kit": "drizzle-kit", "tsx": "tsx", "biome": "@biomejs/biome",
            "wrangler": "wrangler", "changeset": "@changesets/cli", "eslint": "eslint", "vitest": "vitest", "jest": "jest"}

ENV_EXCLUDE = {"README", "LICENSE", "TODO", "FIXME", "MIT", "API", "URL", "URI", "JSON", "YAML", "TOML", "HTML", "CSS",
               "HTTP", "HTTPS", "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRUE", "FALSE", "NULL", "NONE",
               "NOTE", "TIP", "WARNING", "IMPORTANT", "CAUTION", "SPDX", "UTF", "UTF8", "ASCII", "SQL", "CLI", "SDK",
               "CI", "CD", "OK", "ID", "UUID", "AND", "OR", "NOT", "EOF", "PR", "PRS", "GPU", "CPU", "RAM", "OS", "UI",
               "UX", "AWS", "GCP", "JWT", "CSV", "PDF", "PNG", "SVG", "DNS", "TLS", "SSL", "SSH", "TCP", "UDP", "IP",
               "LLM", "AI", "ML", "NPM", "REST", "CRUD", "ISO", "USD", "EUR", "MUST", "SHOULD", "MAY", "REQUIRED",
               "OPTIONAL", "DEFAULT", "YES", "NO", "ON", "OFF", "ALL", "ANY", "NEW", "XXX", "HACK", "BUG", "CHANGELOG",
               "CONTRIBUTING", "SECURITY", "AUTHORS", "NOTICE", "COPYING", "MAINTAINERS", "CODEOWNERS", "UTF_8",
               "EOL", "LTS", "RFC", "FAQ", "WIP", "TBD", "N_A", "MB", "GB", "KB", "TB", "MS"}
ENV_GENERIC = {"PATH", "HOME", "USER", "USERNAME", "USERPROFILE", "SHELL", "PWD", "OLDPWD", "TERM", "LANG", "LC_ALL",
               "EDITOR", "VISUAL", "TMPDIR", "TEMP", "TMP", "NODE_ENV", "NODE_OPTIONS", "PYTHONPATH",
               "PYTHONUNBUFFERED", "PYTHONDONTWRITEBYTECODE", "PYTHONIOENCODING", "PYTHONUTF8", "VIRTUAL_ENV",
               "NO_COLOR", "FORCE_COLOR", "CI", "GOPATH", "GOOS", "GOARCH", "GOBIN", "GOPROXY", "CGO_ENABLED",
               "GO111MODULE", "RUST_LOG", "RUST_BACKTRACE", "CARGO_HOME", "JAVA_HOME", "ANDROID_HOME", "ANDROID_SDK_ROOT",
               "CUDA_VISIBLE_DEVICES", "CUDA_HOME", "LD_LIBRARY_PATH", "DYLD_LIBRARY_PATH", "HOSTNAME", "APPDATA",
               "LOCALAPPDATA", "PROGRAMFILES", "SYSTEMROOT", "COMSPEC", "PSMODULEPATH", "XDG_CONFIG_HOME",
               "XDG_DATA_HOME", "XDG_CACHE_HOME", "PIP_INDEX_URL", "UV_INDEX_URL", "DOCKER_HOST", "DOCKER_BUILDKIT",
               "COMPOSE_PROJECT_NAME", "KUBECONFIG", "SSH_AUTH_SOCK", "DISPLAY", "OMP_NUM_THREADS", "MAKEFLAGS",
               "DEBIAN_FRONTEND", "TZ", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "BROWSER", "PAGER", "COLUMNS",
               "LINES", "RANDOM", "SECONDS", "UID", "EUID", "PPID", "IFS", "PS1", "SHLVL", "CC", "CXX", "CFLAGS",
               "LDFLAGS", "CPPFLAGS", "PKG_CONFIG_PATH", "PYTORCH_CUDA_ALLOC_CONF", "TOKENIZERS_PARALLELISM"}
ENV_GENERIC_PREFIX = ("GITHUB_", "RUNNER_", "npm_", "NPM_CONFIG_", "ACTIONS_", "VERCEL_", "NETLIFY_", "LC_",
                      "XDG_", "CONDA_", "PYENV_", "NVM_", "HOMEBREW_", "BUILDKITE_", "CIRCLE_", "TRAVIS_", "GITLAB_")
IMPLICIT_ENV = {  # read by an SDK without the project spelling the name out
    "OPENAI_API_KEY": ("openai", "@ai-sdk/openai", "langchain-openai", "@langchain/openai", "litellm"),
    "OPENAI_BASE_URL": ("openai",), "OPENAI_ORG_ID": ("openai",),
    "ANTHROPIC_API_KEY": ("anthropic", "@anthropic-ai/sdk", "@ai-sdk/anthropic", "langchain-anthropic", "litellm",
                          "claude-agent-sdk", "@anthropic-ai/claude-agent-sdk"),
    "HF_TOKEN": ("huggingface-hub", "transformers", "datasets", "diffusers", "@huggingface/inference"),
    "HUGGING_FACE_HUB_TOKEN": ("huggingface-hub", "transformers", "datasets"),
    "HF_HOME": ("huggingface-hub", "transformers", "datasets"),
    "AWS_ACCESS_KEY_ID": ("boto3", "botocore", "aws-sdk", "@aws-sdk/", "aws-config"),
    "AWS_SECRET_ACCESS_KEY": ("boto3", "botocore", "aws-sdk", "@aws-sdk/", "aws-config"),
    "AWS_SESSION_TOKEN": ("boto3", "botocore", "aws-sdk", "@aws-sdk/"),
    "AWS_REGION": ("boto3", "botocore", "aws-sdk", "@aws-sdk/", "aws-config"),
    "AWS_DEFAULT_REGION": ("boto3", "botocore", "aws-sdk", "@aws-sdk/"),
    "AWS_PROFILE": ("boto3", "botocore", "aws-sdk", "@aws-sdk/"),
    "GOOGLE_APPLICATION_CREDENTIALS": ("google-", "@google-cloud/", "firebase-admin"),
    "GOOGLE_API_KEY": ("google-genai", "google-generativeai", "@google/genai", "langchain-google"),
    "GEMINI_API_KEY": ("google-genai", "@google/genai"),
    "GROQ_API_KEY": ("groq",), "MISTRAL_API_KEY": ("mistralai", "@mistralai/"), "COHERE_API_KEY": ("cohere",),
    "REPLICATE_API_TOKEN": ("replicate",), "PINECONE_API_KEY": ("pinecone",), "SENTRY_DSN": ("sentry",),
    "WANDB_API_KEY": ("wandb",), "TOGETHER_API_KEY": ("together",), "AZURE_OPENAI_API_KEY": ("openai",),
    "LANGCHAIN_API_KEY": ("langchain", "langsmith"), "LANGSMITH_API_KEY": ("langsmith", "langchain"),
}
GITHUB_ROUTE = re.compile(r"^(\.\./)+(actions|issues|pulls|wiki|releases|discussions|blob|tree|graphs|network|"
                          r"stargazers|fork|security|projects|compare|commits|labels|milestones|tags|branches)(/|$)")
PLACEHOLDER = re.compile(r"[<>{}]|your[-_]|path/to|\bOWNER\b|\bUSER(NAME)?/|example\.com|\.\.\.|…", re.I)
ENV_NAME = re.compile(r"^[A-Z][A-Z0-9]*_[A-Z0-9_]*[A-Z0-9]$")
ENV_WORD = re.compile(r"^[A-Z][A-Z0-9]{2,}$")
PROMPT = re.compile(r"^\s*(?:\([\w.\-]+\)\s*)?(?:[\w.\-]+@[\w.\-]+(?::[^\s$#>]*)?\s*)?"
                    r"(?:\$|%|❯|➜|>|PS(?: [^>]*)?>|[A-Za-z]:\[^>]*>)(?:\s+|$)")
WEAK_PROMPT = re.compile(r"^\s*>(?:\s+|$)")  # a bare "> " is also npm/yarn output, so it loses to $ / PS> prompts


def prompt_lines(texts):
    """Which lines carry a shell prompt. Bare '>' prompts count only when no stronger prompt is present."""
    hits = [bool(PROMPT.match(t)) and not t.lstrip().startswith(">>") for t in texts]
    strong = [h and not WEAK_PROMPT.match(t) for h, t in zip(hits, texts)]
    chosen = strong if any(strong) else hits
    if not any(PROMPT.sub("", t, count=1).strip() for t, h in zip(texts, chosen) if h):
        return [False] * len(texts)
    return chosen


def norm_pkg(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.strip().lower())


def find_git_top(p: Path):
    for d in [p] + list(p.parents):
        if (d / ".git").exists():
            return d
    return None


def normalize_remote(url: str) -> str:
    u = url.strip().lower()
    u = re.sub(r"^git\+", "", u)
    u = re.sub(r"^[a-z]+://", "", u)
    u = re.sub(r"^[^@/]+@", "", u)  # user@ / git@
    u = u.replace(":", "/", 1) if re.match(r"^[\w.\-]+:[^/\d]", u) else u
    u = re.sub(r"\.git/?$", "", u.rstrip("/"))
    return u.rstrip("/")


# --------------------------------------------------------------------------- repo index
class Repo:
    """Everything the checks need to know about the repository, gathered lazily."""

    def __init__(self, root: Path, readme: Path):
        self.root = root.resolve()
        self.top = find_git_top(self.root) or self.root
        self.root_rel = "" if self.top == self.root else self.root.relative_to(self.top).as_posix()
        rp = readme.resolve()
        try:
            self.readme_dir = rp.parent.relative_to(self.top).as_posix()
            if self.readme_dir == ".":
                self.readme_dir = ""
        except ValueError:
            self.readme_dir = self.root_rel
        self.readme_abs = rp
        try:
            self.facts = analyze(self.root)
        except Exception:  # pragma: no cover - analyzer must never take the checker down
            self.facts = {}
        self._ls_cache: dict = {}
        self.files = []  # top-relative posix paths under root
        self.dirs = set()
        count = 0
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            base = Path(dirpath).relative_to(self.top).as_posix()
            base = "" if base == "." else base
            for d in dirnames:
                self.dirs.add(f"{base}/{d}" if base else d)
            for f in filenames:
                count += 1
                if count > 50000:
                    break
                self.files.append(f"{base}/{f}" if base else f)
        self.by_name: dict = {}
        for f in self.files:
            self.by_name.setdefault(f.rsplit("/", 1)[-1], []).append(f)
        self._corpus = None
        self._manifests = None
        remote = (self.facts.get("git") or {}).get("url")
        self.remote = normalize_remote(remote) if remote else None
        names = {self.root.name.lower(), self.top.name.lower()}
        if self.remote:
            names.add(self.remote.rsplit("/", 1)[-1])
        if (self.facts.get("package") or {}).get("name"):
            names.add(str(self.facts["package"]["name"]).lower().split("/")[-1])
        self.repo_names = {n for n in names if n}

    # ---- paths -----------------------------------------------------------------
    def _ls(self, d: Path):
        key = str(d)
        if key not in self._ls_cache:
            try:
                self._ls_cache[key] = set(os.listdir(d))
            except OSError:
                self._ls_cache[key] = set()
        return self._ls_cache[key]

    def exists(self, trel: str):
        """Exact-case existence of a top-relative path. None when it points outside the checkout."""
        trel = posixpath.normpath(trel) if trel else ""
        if trel in ("", "."):
            return True
        if trel.startswith("..") or trel.startswith("/"):
            return None
        cur = self.top
        for part in trel.split("/"):
            if part not in self._ls(cur):
                return False
            cur = cur / part
        return True

    def is_dir(self, trel: str) -> bool:
        return bool(self.exists(trel)) and (self.top / trel).is_dir()

    def show(self, trel: str) -> str:
        if not self.root_rel:
            return trel or "."
        if trel == self.root_rel:
            return "."
        if trel.startswith(self.root_rel + "/"):
            return trel[len(self.root_rel) + 1:]
        return posixpath.relpath(trel or ".", self.root_rel)

    def join(self, base, p: str) -> str:
        return posixpath.normpath(posixpath.join(base or "", p)) if p else (base or "")

    def under_root(self, trel: str) -> str:
        return self.join(self.root_rel, trel)

    def suffix_match(self, p: str):
        p = p.strip("/")
        for f in self.files:
            if f == p or f.endswith("/" + p):
                return f
        for d in self.dirs:
            if d == p or d.endswith("/" + p):
                return d
        return None

    # ---- text search -----------------------------------------------------------
    @property
    def corpus(self):
        """[(top-rel path, text, is_source)] for every non-Markdown text file."""
        if self._corpus is None:
            out = []
            for f in self.files:
                name = f.rsplit("/", 1)[-1]
                ext = os.path.splitext(name)[1].lower()
                if ext in BINARY_EXT or ext in MD_EXT:
                    continue
                p = self.top / f
                try:
                    if p.stat().st_size > 1_000_000:
                        continue
                except OSError:
                    continue
                text = read_text(p, 1_000_000)
                if "\x00" in text[:2000]:
                    continue
                src = ext in SOURCE_EXT or (not ext and text.startswith("#!"))
                out.append((f, text, src))
            self._corpus = out
        return self._corpus

    def grep(self, pattern, source_only=False, prefer=None):
        """First file whose text matches; `prefer` (top-rel) is tried first."""
        rx = re.compile(pattern) if isinstance(pattern, str) else pattern
        items = self.corpus
        if prefer:
            items = sorted(items, key=lambda it: it[0] != prefer)
        for f, text, src in items:
            if source_only and not src:
                continue
            if rx.search(text):
                return f
        return None

    # ---- manifests -------------------------------------------------------------
    @property
    def m(self):
        if self._manifests is None:
            self._manifests = self._load_manifests()
        return self._manifests

    def _load_manifests(self):
        m = {"pkg_json": [], "scripts": {}, "js_deps": set(), "js_bins": {}, "js_names": set(), "pms": {},
             "py_names": set(), "py_deps": set(), "py_bins": {}, "pyprojects": [], "cargo": [], "cargo_names": set(),
             "cargo_bins": set(), "cargo_examples": set(), "deps": set()}
        for f in self.files:
            name = f.rsplit("/", 1)[-1]
            d = f.rsplit("/", 1)[0] if "/" in f else ""
            if name in LOCKFILES:
                m["pms"].setdefault(LOCKFILES[name], f)
            elif name == "package.json":
                pkg = load_json(self.top / f) or {}
                if not isinstance(pkg, dict):
                    continue
                m["pkg_json"].append(f)
                for k in (pkg.get("scripts") or {}):
                    m["scripts"].setdefault(k, f)
                for sect in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
                    m["js_deps"].update((pkg.get(sect) or {}).keys())
                if pkg.get("name"):
                    m["js_names"].add(str(pkg["name"]))
                b = pkg.get("bin")
                if isinstance(b, str) and pkg.get("name"):
                    m["js_bins"][str(pkg["name"]).split("/")[-1]] = self.join(d, b)
                elif isinstance(b, dict):
                    for k, v in b.items():
                        m["js_bins"][k] = self.join(d, str(v))
                pmf = str(pkg.get("packageManager") or "")
                if pmf.split("@")[0] in JS_PMS:
                    m["pms"].setdefault(pmf.split("@")[0], f)
            elif name == "pyproject.toml":
                data = load_toml(self.top / f) or {}
                m["pyprojects"].append(f)
                proj = data.get("project") or {}
                tool = data.get("tool") or {}
                poetry = tool.get("poetry") or {}
                for n in (proj.get("name"), poetry.get("name")):
                    if n:
                        m["py_names"].add(norm_pkg(str(n)))
                m["py_deps"].update(norm_pkg(x) for x in dep_names(proj.get("dependencies")))
                for grp in list((proj.get("optional-dependencies") or {}).values()) + \
                        list((data.get("dependency-groups") or {}).values()):
                    m["py_deps"].update(norm_pkg(x) for x in dep_names([g for g in grp if isinstance(g, str)]))
                for sect in ("dependencies", "dev-dependencies"):
                    m["py_deps"].update(norm_pkg(x) for x in (poetry.get(sect) or {}))
                for grp in (poetry.get("group") or {}).values():
                    m["py_deps"].update(norm_pkg(x) for x in ((grp or {}).get("dependencies") or {}))
                m["py_deps"].update(norm_pkg(x) for x in dep_names((tool.get("uv") or {}).get("dev-dependencies")))
                for sect in ("scripts", "gui-scripts"):
                    for k, v in (proj.get(sect) or {}).items():
                        m["py_bins"][k] = (f, str(v))
                for k, v in (poetry.get("scripts") or {}).items():
                    m["py_bins"][k] = (f, str(v))
            elif re.match(r"^requirements.*\.(txt|in)$", name) or (d.endswith("requirements") and name.endswith(".txt")):
                m["py_deps"].update(norm_pkg(x) for x in parse_requirements(read_text(self.top / f)))
            elif name == "setup.py":
                mm = re.search(r"name\s*=\s*['\"]([^'\"]+)", read_text(self.top / f))
                if mm:
                    m["py_names"].add(norm_pkg(mm.group(1)))
            elif name == "setup.cfg":
                txt = read_text(self.top / f)
                mm = re.search(r"^name\s*=\s*(\S+)", txt, re.M)
                if mm:
                    m["py_names"].add(norm_pkg(mm.group(1)))
            elif name == "Pipfile":
                m["py_deps"].update(norm_pkg(x) for x in re.findall(r"^\"?([A-Za-z0-9][\w.\-]*)\"?\s*=", read_text(self.top / f), re.M))
            elif name in ("environment.yml", "environment.yaml"):
                m["py_deps"].update(norm_pkg(x) for x in re.findall(r"^\s*-\s*([A-Za-z0-9][\w.\-]*)", read_text(self.top / f), re.M))
            elif name == "Cargo.toml":
                data = load_toml(self.top / f) or {}
                m["cargo"].append(f)
                pk = data.get("package") or {}
                if pk.get("name"):
                    m["cargo_names"].add(str(pk["name"]))
                    if self.exists(self.join(d, "src/main.rs")):
                        m["cargo_bins"].add(str(pk["name"]))
                for b in data.get("bin") or []:
                    if isinstance(b, dict) and b.get("name"):
                        m["cargo_bins"].add(str(b["name"]))
                for b in data.get("example") or []:
                    if isinstance(b, dict) and b.get("name"):
                        m["cargo_examples"].add(str(b["name"]))
                m["deps"].update(norm_pkg(x) for x in (data.get("dependencies") or {}))
        for f in self.files:
            mm = re.search(r"(?:^|/)src/bin/([\w\-]+)(?:\.rs|/main\.rs)$", f)
            if mm:
                m["cargo_bins"].add(mm.group(1))
            mm = re.search(r"(?:^|/)examples/([\w\-]+)(?:\.rs|/main\.rs)$", f)
            if mm:
                m["cargo_examples"].add(mm.group(1))
        m["deps"].update(norm_pkg(x) for x in m["js_deps"])
        m["deps"].update(m["py_deps"])
        bins = {}
        for k, v in (self.facts.get("bins") or {}).items():
            bins[k] = f"declared in {self.facts.get('manifests', ['manifest'])[0] if self.facts.get('manifests') else 'manifest'}"
        for k, v in m["js_bins"].items():
            bins[k] = f"package.json bin -> {self.show(v)}"
        for k, (f, v) in m["py_bins"].items():
            bins[k] = f"{self.show(f)} [project.scripts] -> {v}"
        for k in m["cargo_bins"]:
            bins.setdefault(k, "Cargo binary")
        for k, v in (self.facts.get("bins") or {}).items():
            if isinstance(v, str) and v.startswith("./cmd/"):
                bins[k] = f"Go command {v}"
        m["bins"] = bins
        return m

    def has_dep(self, *names) -> bool:
        deps = self.m["deps"] | {norm_pkg(x) for x in self.m["js_deps"]}
        for n in names:
            nn = norm_pkg(n)
            if n.endswith("/") or n.endswith("-"):
                if any(d.startswith(norm_pkg(n.rstrip("/-"))) for d in deps) or any(d.startswith(n) for d in self.m["js_deps"]):
                    return True
            elif nn in deps:
                return True
        return False

    def files_named(self, *names):
        out = []
        for n in names:
            out += self.by_name.get(n, [])
        return out


# --------------------------------------------------------------------------- markdown parsing
def blank_html_comments(lines, in_code):
    """Replace <!-- ... --> outside code with spaces, keeping line numbers."""
    out, open_ = [], False
    for i, line in enumerate(lines):
        if in_code[i]:
            out.append(line)
            continue
        res, j = "", 0
        while j < len(line):
            if open_:
                k = line.find("-->", j)
                if k < 0:
                    j = len(line)
                    break
                open_, j = False, k + 3
            else:
                k = line.find("<!--", j)
                if k < 0:
                    res += line[j:]
                    break
                res += line[j:k]
                open_, j = True, k + 4
        out.append(res)
    return out


def parse_fences(lines):
    """Return (blocks, in_code). blocks: {lang, open_line, lines: [(lineno, text)]}."""
    blocks, in_code = [], [False] * len(lines)
    cur = None
    for i, line in enumerate(lines):
        m = re.match(r"^(\s*)(`{3,}|~{3,})\s*(.*)$", line)
        if cur is None:
            if m and not (m.group(2)[0] == "`" and "`" in m.group(3)):
                info = m.group(3).strip().lower()
                info = re.sub(r"^\{\.?|\}$", "", info)
                lang = re.split(r"[\s,{]", info, maxsplit=1)[0] if info else ""
                cur = {"lang": lang, "open_line": i + 1, "fence": m.group(2), "lines": []}
                in_code[i] = True
            continue
        in_code[i] = True
        if m and m.group(2)[0] == cur["fence"][0] and len(m.group(2)) >= len(cur["fence"]) and not m.group(3).strip():
            blocks.append(cur)
            cur = None
            continue
        cur["lines"].append((i + 1, line))
    if cur is not None:
        blocks.append(cur)
    return blocks, in_code


def split_statements(line: str):
    """Split on && || ; & (quote-aware), keep the first stage of each pipe, drop # comments."""
    stmts, cur, quote, depth, piped = [], "", None, 0, False
    i, n = 0, len(line)

    def flush():
        nonlocal cur, piped
        if not piped and cur.strip():
            stmts.append(cur.strip())
        cur, piped = "", False

    while i < n:
        c = line[i]
        if quote:
            cur += c
            if c == "\\" and quote == '"' and i + 1 < n:
                cur += line[i + 1]
                i += 2
                continue
            if c == quote:
                quote = None
            i += 1
            continue
        if c in "'\"":
            quote = c
            cur += c
        elif c == "$" and line[i + 1:i + 2] == "(":
            depth += 1
            cur += "$("
            i += 2
            continue
        elif depth:
            depth += c == "("
            depth -= c == ")"
            cur += c
        elif c == "#" and (i == 0 or line[i - 1].isspace()):
            break
        elif line[i:i + 2] in ("&&", "||"):
            flush()
            i += 2
            continue
        elif c == ";":
            flush()
        elif c == "&" and line[i - 1:i] != ">" and line[i + 1:i + 2] != ">":
            flush()
        elif c == "|":
            if not piped and cur.strip():
                stmts.append(cur.strip())
            cur, piped = "", True
        else:
            cur += c
        i += 1
    flush()
    return stmts


def tokenize(stmt: str):
    try:
        return shlex.split(stmt, posix=True)
    except ValueError:
        return stmt.split()


def strip_redirects(tokens):
    out, skip = [], False
    for t in tokens:
        if skip:
            skip = False
            continue
        if re.fullmatch(r"\d*>>?|&>>?|<", t):
            skip = True
            continue
        if re.fullmatch(r"\d*>&\d*|\d*>>?\S+|&>>?\S+", t) or (t.startswith("<") and not t.endswith(">")):
            continue
        out.append(t)
    return out


def is_placeholder(s: str) -> bool:
    return bool(PLACEHOLDER.search(s))


# --------------------------------------------------------------------------- the checker
class Ctx:
    def __init__(self, cwd):
        self.cwd = cwd  # top-relative, None when unknown


class Verifier:
    def __init__(self, repo: Repo):
        self.r = repo
        self.claims = []
        self._seen = {}
        self.clone_dirs = set()
        self.created = set()  # tokens earlier commands may have created (mkdir, scaffolders, clones)
        self.built_tags = set()
        self.line = 0
        self.stmt = ""

    # ---- recording ---------------------------------------------------------
    def add(self, kind, text, status, evidence, scope=None, line=None):
        key = (kind, text if kind != "flag" else (text, scope))
        if key in self._seen:
            return
        c = {"kind": kind, "text": text, "line": line or self.line, "status": status, "evidence": evidence}
        self._seen[key] = c
        self.claims.append(c)

    def cmd(self, status, evidence, kind="command", text=None):
        self.add(kind, text or self.stmt, status, evidence)

    # ---- path helpers --------------------------------------------------------
    def locate(self, p: str, ctx: Ctx, kinds=("file", "dir")):
        """Resolve a path an instruction uses. Returns (status, evidence, top-rel or None)."""
        p = p.strip().strip("'\"").replace("\\", "/")
        if not p:
            return "generic", "empty path", None
        if p.startswith(("~", "$", "%")) or re.match(r"^[A-Za-z]:/", p) or p.startswith("/"):
            return "generic", "outside the repository", None
        if is_placeholder(p):
            return "unverifiable", "placeholder", None
        if any(ch in p for ch in "*?["):
            return "unverifiable", "glob pattern", None
        p = p.rstrip("/") or "."
        bases = []
        if ctx.cwd is not None:
            bases.append(ctx.cwd)
        for b in (self.r.readme_dir, self.r.root_rel):
            if b not in bases:
                bases.append(b)
        first = p.split("/", 1)[0]
        if first in self.clone_dirs or (first.lower() in self.r.repo_names and not self.r.exists(self.r.join(bases[0], first))):
            rest = p.split("/", 1)[1] if "/" in p else ""
            if self.r.exists(rest) or not rest:
                return "verified", f"{rest or '.'} (inside the cloned repo)", rest
        for b in bases:
            t = self.r.join(b, p)
            ex = self.r.exists(t)
            if ex:
                kind_ok = ("dir" in kinds and self.r.is_dir(t)) or ("file" in kinds and not self.r.is_dir(t))
                if kind_ok or kinds == ("file", "dir"):
                    return "verified", f"{self.r.show(t)} exists", t
        if ctx.cwd is None:
            return "unverifiable", "working directory unknown after an earlier cd", None
        if first in BUILD_DIRS or "/target/" in "/" + p or p.split("/")[0] in ("dist", "build", "out"):
            return "unverifiable", "build output", None
        if p in self.created or first in self.created or p.rsplit("/", 1)[-1] in self.created:
            return "unverifiable", "created by an earlier command", None
        if "/" not in p and self.r.by_name.get(p):
            where = self.r.by_name[p][0]
            return "verified", f"exists at {self.r.show(where)} (not in this folder)", where
        return "not_found", f"no {p} in {self.r.show(bases[0]) if bases[0] else '.'}", None

    # ---- flags -----------------------------------------------------------------
    def flags(self, args, prog_label, prefer=None):
        for a in args:
            if not a.startswith("--") or len(a) < 3 or a == "--":
                continue
            flag = a.split("=", 1)[0]
            if not re.fullmatch(r"--[A-Za-z0-9][\w\-.]*", flag):
                continue
            if flag in ("--help", "--version"):
                self.add("flag", flag, "generic", f"standard {prog_label} flag", scope=prog_label)
                continue
            found = self.find_flag(flag, prefer)
            if found:
                self.add("flag", flag, "verified", f"{found} ({prog_label})", scope=prog_label)
            else:
                self.add("flag", flag, "not_found", f"{flag} not defined in any source file ({prog_label})", scope=prog_label)

    def find_flag(self, flag, prefer=None):
        name = flag[2:]
        rx = re.compile(r"(?<![\w-])" + re.escape(flag) + r"(?![\w-])")
        f = self.r.grep(rx, source_only=True, prefer=prefer)
        if f:
            return f"{self.r.show(f)} defines {flag}"
        if name.startswith("no-") and self.r.grep(re.compile(r"(?<![\w-])--" + re.escape(name[3:]) + r"(?![\w-])"), source_only=True):
            return f"--{name[3:]} is defined (negated form)"
        q = re.compile(r"[\"'`]" + re.escape(name) + r"[\"'`]")
        for path, text, src in self.r.corpus:
            if src and path.endswith((".go", ".js", ".ts", ".mjs", ".cjs", ".rs", ".rb", ".java", ".kt", ".cs", ".py")) and q.search(text):
                return f"{self.r.show(path)} defines \"{name}\""
        snake = name.replace("-", "_")
        ident = re.compile(r"(?<![\w])" + re.escape(snake) + r"\s*:")
        for path, text, src in self.r.corpus:
            if path.endswith(".rs") and ident.search(text) and re.search(r"clap|structopt|argh", text):
                return f"{self.r.show(path)} field {snake} (clap long flag)"
            if path.endswith(".py") and "typer" in text and re.search(r"\b" + re.escape(snake) + r"\s*[:=]", text):
                return f"{self.r.show(path)} parameter {snake} (typer option)"
        return None

    # ---- dispatch ----------------------------------------------------------------
    def command(self, stmt, ctx: Ctx, line):
        self.line, self.stmt = line, re.sub(r"\s+", " ", stmt).strip()
        tokens = strip_redirects(tokenize(stmt))
        # leading VAR=value, sudo, env, time ...
        while tokens:
            t = tokens[0]
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", t):
                tokens = tokens[1:]
            elif t in ("sudo", "doas", "time", "nohup", "command", "builtin", "noglob"):
                tokens = tokens[1:]
                while tokens and t in ("sudo", "doas") and tokens[0].startswith("-"):
                    tokens = tokens[1:]
            elif t == "env" and len(tokens) > 1:
                tokens = tokens[1:]
            elif t.startswith("$env:") or re.match(r"^\$[A-Za-z_]\w*\s*=?$", t):
                return self.cmd("generic", "sets a variable")
            else:
                break
        if not tokens:
            return
        self.dispatch(tokens, ctx)

    def dispatch(self, tokens, ctx: Ctx):
        raw = tokens[0]
        prog = raw.replace("\\", "/")
        low = prog.lower()
        if low.endswith(".exe"):
            low = low[:-4]
        base = low.rsplit("/", 1)[-1]
        if re.fullmatch(r"python(\d+(\.\d+)?)?w?|py", base):
            base = "python"
        elif re.fullmatch(r"pip\d+(\.\d+)?", base):
            base = "pip"
        args = tokens[1:]
        if base == "docker-compose":
            return self.docker(["compose"] + args, ctx)
        if low in ("./gradlew", "gradlew", "./gradlew.bat", "gradlew.bat", "./mvnw", "mvnw", "./mvnw.cmd", "mvnw.cmd"):
            return self.wrapper(prog, ctx)
        handler = {
            "npm": self.js, "pnpm": self.js, "yarn": self.js, "bun": self.js, "npx": self.npx, "bunx": self.npx,
            "pip": self.pip, "pipx": self.pipx, "uv": self.uv, "uvx": self.uvx, "poetry": self.poetry,
            "pdm": self.pdm, "pipenv": self.pipenv, "hatch": self.hatch, "conda": self.conda, "mamba": self.conda,
            "micromamba": self.conda, "python": self.python, "make": self.make, "just": self.just, "task": self.task,
            "cargo": self.cargo, "go": self.go, "docker": self.docker, "podman": self.docker, "git": self.git,
            "cd": self.cd, "pushd": self.cd, "set-location": self.cd, "sl": self.cd, "chdir": self.cd,
            "cp": self.copy, "mv": self.copy, "copy": self.copy, "move": self.copy, "copy-item": self.copy,
            "move-item": self.copy, "node": self.node, "nodejs": self.node, "ts-node": self.node, "tsx": self.node,
            "deno": self.deno, "bash": self.shell, "sh": self.shell, "zsh": self.shell, "pwsh": self.shell,
            "powershell": self.shell, "fish": self.shell, "pytest": self.pytest, "pre-commit": self.precommit,
            "tox": self.tox, "nox": self.nox, "uvicorn": self.asgi, "gunicorn": self.asgi, "hypercorn": self.asgi,
            "streamlit": self.streamlit, "fastapi": self.fastapi, "kubectl": self.kubectl, "helm": self.helm,
            "terraform": self.terraform, "cmake": self.cmake, "meson": self.meson, "mvn": self.maven,
            "gradle": self.gradle, "dotnet": self.dotnet, "flutter": self.flutter, "dart": self.flutter,
            "mix": self.mix, "bundle": self.bundle, "rails": self.rails, "rake": self.rails, "composer": self.composer,
            "php": self.php, "swift": self.swift, "zig": self.zig, "stack": self.stack, "cabal": self.cabal,
        }.get(base)
        if prog.startswith(("./", "../", ".\\")) or (("/" in prog) and base not in ("python", "pip", "node") and handler is None):
            return self.run_file(prog, args, ctx)
        if handler:
            return handler(args, ctx) if handler not in (self.js,) else handler(base, args, ctx)
        bins = self.r.m["bins"]
        if raw in bins:
            self.cmd("verified", bins[raw])
            return self.flags(args, raw)
        if base in DEV_TOOLS:
            return self.devtool(base, args)
        if base in GENERIC_PROGRAMS:
            if base in ("mkdir", "md", "touch", "new-item"):
                self.created.update(a.strip("/") for a in args if not a.startswith("-"))
            return self.cmd("generic", "needs nothing from the repo")
        return self.cmd("unverifiable", f"'{raw}' is not a tool this checker knows")

    # ---- JavaScript --------------------------------------------------------------
    def positional(self, args, value_opts=()):
        out, skip = [], False
        for a in args:
            if skip:
                skip = False
                continue
            if a in value_opts:
                skip = True
                continue
            if a.startswith("-"):
                continue
            out.append(a)
        return out

    def pm_claim(self, pm):
        m = self.r.m
        if not m["pkg_json"]:
            return
        pms = m["pms"]
        if pms:
            if pm in pms:
                self.add("package_manager", pm, "verified", f"{self.r.show(pms[pm])} matches {pm}")
            else:
                src = ", ".join(f"{self.r.show(v)}" for v in pms.values())
                self.add("package_manager", pm, "not_found", f"repo uses {'/'.join(sorted(pms))} ({src}), not {pm}")
        elif pm == "npm":
            self.add("package_manager", pm, "verified", "no lockfile; npm is the default")
        else:
            self.add("package_manager", pm, "unverifiable", f"no lockfile or packageManager field names {pm}")

    def script_claim(self, name, pm):
        m = self.r.m
        if name in m["scripts"]:
            return self.cmd("verified", f"{self.r.show(m['scripts'][name])} scripts.{name}", kind="script")
        if not m["pkg_json"]:
            return self.cmd("not_found", "no package.json in the repo", kind="script")
        have = ", ".join(sorted(m["scripts"])[:12]) or "none"
        return self.cmd("not_found", f"no '{name}' script in package.json (scripts: {have})", kind="script")

    def js(self, pm, args, ctx):
        m = self.r.m
        if any(a in ("-g", "--global", "--location=global") for a in args) or (args[:1] == ["global"]):
            return self.cmd("generic", "global install")
        if not args:
            if pm == "yarn":
                return self.js_install(pm)
            return self.cmd("generic", f"bare {pm}")
        if args[0] in ("-v", "--version", "-h", "--help", "help"):
            return self.cmd("generic", "version/help")
        pos = self.positional(args, NPM_VALUE_OPTS | ({"-w"} if pm == "npm" else set()))
        if not pos:
            return self.js_install(pm) if pm == "yarn" else self.cmd("generic", f"{pm} option only")
        sub, rest = pos[0], pos[1:]
        if pm == "yarn" and sub == "workspace" and len(rest) >= 2:
            sub, rest = rest[1], rest[2:]
        if sub in ("install", "i", "ci", "add", "isntall") and not (pm == "npm" and sub == "add"):
            if rest:
                return self.named_js_install(rest)
            if sub == "add":
                return self.cmd("generic", f"{pm} add without a package")
            return self.js_install(pm)
        if pm == "npm" and sub == "add":
            return self.named_js_install(rest)
        if sub in ("run", "run-script"):
            if not rest:
                return self.cmd("generic", "lists scripts")
            name = rest[0]
            if pm == "bun" and (os.path.splitext(name)[1] or "/" in name):
                return self.file_cmd(name, ctx, rest[1:])
            self.pm_claim(pm)
            return self.script_claim(name, pm)
        if sub in ("test", "t", "start", "stop", "restart") and (pm == "npm" or sub in ("test", "start")):
            name = {"t": "test"}.get(sub, sub)
            self.pm_claim(pm)
            if pm == "bun" and sub == "test" and name not in m["scripts"]:
                return self.cmd("unverifiable", "bun's built-in test runner", kind="script")
            if name == "start" and name not in m["scripts"]:
                for b in (ctx.cwd, self.r.readme_dir, self.r.root_rel):
                    if b is not None and self.r.exists(self.r.join(b, "server.js")):
                        return self.cmd("verified", "npm start falls back to server.js", kind="script")
            return self.script_claim(name, pm)
        if sub in ("exec", "x", "dlx") and pm != "npm" or (pm == "npm" and sub == "exec"):
            return self.npx(rest, ctx)
        if sub == "create" or sub == "init":
            self.created.update(a for a in rest if not a.startswith("-"))
            return self.cmd("generic", "scaffolds a new project")
        if pm != "npm" and sub not in NPM_BUILTIN:
            if pm == "bun" and (os.path.splitext(sub)[1] in (".ts", ".js", ".tsx", ".jsx", ".mjs") or "/" in sub):
                return self.file_cmd(sub, ctx, rest)
            if sub in m["scripts"]:
                self.pm_claim(pm)
                return self.script_claim(sub, pm)
            if self.r.has_dep(sub) or sub in m["bins"] or (sub in NPX_BINS and self.r.has_dep(NPX_BINS[sub])):
                return self.cmd("verified", f"runs the {sub} binary from a dependency")
            self.pm_claim(pm)
            return self.script_claim(sub, pm)
        if pm == "bun" and sub in ("build", "test"):
            return self.cmd("unverifiable", f"bun {sub} built-in")
        return self.cmd("generic", f"{pm} {sub} needs nothing from the repo")

    def js_install(self, pm):
        self.pm_claim(pm)
        m = self.r.m
        if m["pkg_json"]:
            return self.cmd("verified", f"{self.r.show(m['pkg_json'][0])} exists")
        return self.cmd("not_found", "no package.json in the repo")

    def named_js_install(self, names):
        m = self.r.m
        for n in names:
            if n.startswith("-"):
                continue
            name = n if not n.startswith("@") else n
            name = re.sub(r"(?<!^)@[^/]*$", "", name)
            if name in m["js_names"]:
                return self.cmd("verified", f"{name} is this project's package")
            if name in m["js_deps"]:
                return self.cmd("verified", f"{name} is a dependency in package.json")
            if is_placeholder(name) or "/" in name and not name.startswith("@"):
                return self.cmd("unverifiable", "local path or placeholder")
            return self.cmd("unverifiable", f"{name} is a third-party package")
        return self.cmd("generic", "no package named")

    def npx(self, args, ctx):
        pos = self.positional(args, {"-p", "--package", "-c", "--call"})
        if not pos:
            return self.cmd("generic", "no package")
        target, rest = pos[0], args[args.index(pos[0]) + 1:] if pos[0] in args else []
        if target.startswith(("./", "../")):
            return self.file_cmd(target, ctx, rest)
        name = re.sub(r"(?<!^)@[^/]*$", "", target)
        m = self.r.m
        if name in m["bins"]:
            self.cmd("verified", m["bins"][name])
            return self.flags(rest, name)
        if name in m["js_deps"] or (name in NPX_BINS and NPX_BINS[name] in m["js_deps"]):
            return self.cmd("verified", f"{name} is a dependency")
        if name in m["js_names"]:
            return self.cmd("verified", f"{name} is this project's package")
        if name.startswith("create-"):
            self.created.update(a for a in rest if not a.startswith("-"))
            return self.cmd("generic", "scaffolds a new project")
        return self.cmd("unverifiable", f"{name} is not a dependency (fetched from the registry)")

    # ---- Python ------------------------------------------------------------------
    def py_manifest(self, ctx, files=("pyproject.toml", "setup.py", "setup.cfg"), d="."):
        st, ev, t = "not_found", "", None
        for f in files:
            st2, ev2, t = self.locate(self.r.join(d, f) if d != "." else f, ctx, kinds=("file",))
            if st2 == "verified":
                return "verified", ev2
            if st2 == "unverifiable":
                st, ev = st2, ev2
        if st == "unverifiable":
            return st, ev
        return "not_found", f"no {'/'.join(files)} in {d if d != '.' else 'this folder'}"

    def pip(self, args, ctx):
        if not args or args[0] in ("--version", "-V", "help", "--help", "freeze", "list", "show", "uninstall", "cache",
                                   "config", "download", "wheel", "check", "inspect", "index", "debug", "hash"):
            return self.cmd("generic", "pip housekeeping")
        if args[0] != "install":
            return self.cmd("generic", f"pip {args[0]}")
        return self.pip_install(args[1:], ctx)

    def pip_install(self, args, ctx, tool="pip"):
        i, results = 0, []
        names = []
        while i < len(args):
            a = args[i]
            if a in ("-r", "--requirement", "-c", "--constraint"):
                if i + 1 < len(args):
                    results.append(self.locate(args[i + 1], ctx, kinds=("file",)))
                i += 2
                continue
            mm = re.match(r"^(?:-r|--requirement=|-c|--constraint=)(.+)$", a)
            if mm:
                results.append(self.locate(mm.group(1), ctx, kinds=("file",)))
            elif a in ("-e", "--editable"):
                if i + 1 < len(args):
                    results.append(self.local_project(args[i + 1], ctx))
                i += 2
                continue
            elif a in ("-i", "--index-url", "--extra-index-url", "-f", "--find-links", "--target", "-t", "--prefix",
                       "--python", "-p", "--platform"):
                i += 2
                continue
            elif a.startswith("-"):
                pass
            elif a in (".",) or a.startswith((".", "/", "~")) or ("/" in a and not a.startswith(("git+", "http"))):
                results.append(self.local_project(a, ctx))
            else:
                names.append(a)
            i += 1
        for st, ev, _ in results:
            if st == "not_found":
                return self.cmd(st, ev)
        if results:
            st, ev, _ = results[0]
            if all(r[0] == "verified" for r in results) and not names:
                return self.cmd("verified", "; ".join(r[1] for r in results))
            if not names:
                return self.cmd(st, ev)
        if not names:
            return self.cmd("generic", "nothing to install")
        m = self.r.m
        for n in names:
            if n.startswith(("git+", "http://", "https://")):
                if self.r.remote and normalize_remote(n.split("@")[0] if n.startswith("git+") else n).startswith(self.r.remote):
                    return self.cmd("verified", "installs this repo from git")
                return self.cmd("unverifiable", "installs from a URL")
            name = norm_pkg(re.split(r"[\[<>=!~;@ ]", n, maxsplit=1)[0])
            if name in ("pip", "setuptools", "wheel", "uv", "pipx", "virtualenv"):
                continue
            if name in m["py_names"]:
                return self.cmd("verified", f"{name} is this project's package")
            if name in m["py_deps"]:
                return self.cmd("verified", f"{name} is a listed dependency")
            if self.r.facts.get("package", {}).get("name") and norm_pkg(str(self.r.facts["package"]["name"])) == name:
                return self.cmd("verified", f"{name} is this project's package")
            return self.cmd("unverifiable", f"{name} is a third-party package")
        return self.cmd("generic", "installs packaging tools")

    def local_project(self, p, ctx):
        p = re.sub(r"\[.*\]$", "", p.strip("'\""))
        st, ev, t = self.locate(p, ctx, kinds=("dir",))
        if st != "verified":
            return st, ev, t
        for f in ("pyproject.toml", "setup.py", "setup.cfg"):
            if self.r.exists(self.r.join(t, f)):
                return "verified", f"{self.r.show(self.r.join(t, f))} exists", t
        return "not_found", f"{self.r.show(t)} has no pyproject.toml/setup.py/setup.cfg", t

    def pipx(self, args, ctx):
        if args[:1] == ["install"] or args[:1] == ["run"]:
            return self.pip_install(args[1:], ctx, tool="pipx")
        return self.cmd("generic", "pipx housekeeping")

    def uv(self, args, ctx):
        if not args:
            return self.cmd("generic", "bare uv")
        sub, rest = args[0], args[1:]
        if sub in ("sync", "lock", "build", "publish", "export", "tree"):
            st, ev = self.py_manifest(ctx, ("pyproject.toml",))
            return self.cmd(st, ev)
        if sub == "pip":
            if rest[:1] in (["install"], ["sync"]):
                return self.pip_install(rest[1:], ctx)
            return self.cmd("generic", "uv pip housekeeping")
        if sub == "run":
            return self.inner_run(rest, ctx, "uv run", {"--with", "--python", "-p", "--group", "--extra", "--env-file", "--package", "--directory", "--project"})
        if sub == "tool":
            if rest[:1] == ["install"]:
                return self.pip_install(rest[1:], ctx)
            if rest[:1] == ["run"]:
                return self.uvx(rest[1:], ctx)
            return self.cmd("generic", "uv tool housekeeping")
        return self.cmd("generic", f"uv {sub}")

    def uvx(self, args, ctx):
        pos = self.positional(args, {"--from", "--with", "--python", "-p"})
        if not pos:
            return self.cmd("generic", "bare uvx")
        name = norm_pkg(re.split(r"[\[@=]", pos[0], maxsplit=1)[0])
        if pos[0] in self.r.m["bins"]:
            self.cmd("verified", self.r.m["bins"][pos[0]])
            return self.flags(args[args.index(pos[0]) + 1:], pos[0])
        if name in self.r.m["py_names"] or name in self.r.m["py_deps"]:
            return self.cmd("verified", f"{name} is this project or a dependency")
        return self.cmd("unverifiable", f"{name} is fetched from PyPI")

    def inner_run(self, rest, ctx, label, value_opts=()):
        pos_idx = None
        skip = False
        for i, a in enumerate(rest):
            if skip:
                skip = False
                continue
            if a in value_opts:
                skip = True
                continue
            if a.startswith("-"):
                continue
            pos_idx = i
            break
        if pos_idx is None:
            return self.cmd("generic", f"bare {label}")
        inner = rest[pos_idx:]
        name = inner[0]
        if name.endswith(".py") or "/" in name:
            return self.file_cmd(name, ctx, inner[1:])
        for pp in self.r.m["pyprojects"]:
            txt = read_text(self.r.top / pp)
            if re.search(r"^\[tool\.(pdm|hatch|poe|rye|taskipy)[^\]]*scripts\]", txt, re.M) and \
                    re.search(r"^\s*\"?" + re.escape(name) + r"\"?\s*=", txt, re.M):
                return self.cmd("verified", f"{self.r.show(pp)} defines script {name}", kind="script")
        self.dispatch(inner, ctx)

    def poetry(self, args, ctx):
        sub = args[0] if args else ""
        if sub in ("install", "lock", "build", "update", "check", "sync", "shell", "env", "show"):
            st, ev = self.py_manifest(ctx, ("pyproject.toml",))
            return self.cmd(st, ev)
        if sub == "run":
            return self.inner_run(args[1:], ctx, "poetry run")
        return self.cmd("generic", f"poetry {sub}".strip())

    def pdm(self, args, ctx):
        sub = args[0] if args else ""
        if sub in ("install", "sync", "lock", "build", "update"):
            st, ev = self.py_manifest(ctx, ("pyproject.toml",))
            return self.cmd(st, ev)
        if sub == "run":
            return self.inner_run(args[1:], ctx, "pdm run")
        return self.cmd("generic", f"pdm {sub}".strip())

    def hatch(self, args, ctx):
        sub = args[0] if args else ""
        if sub == "run":
            return self.inner_run(args[1:], ctx, "hatch run")
        if sub in ("build", "test", "shell", "env", "fmt", "version"):
            st, ev = self.py_manifest(ctx, ("pyproject.toml",))
            return self.cmd(st, ev)
        return self.cmd("generic", f"hatch {sub}".strip())

    def pipenv(self, args, ctx):
        sub = args[0] if args else "install"
        if sub in ("install", "sync", "lock", "update"):
            names = [a for a in args[1:] if not a.startswith("-")]
            if names and sub == "install":
                return self.pip_install(names, ctx)
            st, ev = self.py_manifest(ctx, ("Pipfile", "requirements.txt"))
            return self.cmd(st, ev)
        if sub == "run":
            return self.inner_run(args[1:], ctx, "pipenv run")
        return self.cmd("generic", f"pipenv {sub}")

    def conda(self, args, ctx):
        if args[:2] in (["env", "create"], ["env", "update"]) or args[:1] in (["install"], ["create"]):
            files = [args[i + 1] for i, a in enumerate(args[:-1]) if a in ("-f", "--file")]
            files += [a.split("=", 1)[1] for a in args if a.startswith("--file=")]
            if files:
                st, ev, _ = self.locate(files[0], ctx, kinds=("file",))
                return self.cmd(st, ev)
            if args[:1] == ["env"]:
                st, ev = self.py_manifest(ctx, ("environment.yml", "environment.yaml"))
                return self.cmd(st, ev)
        return self.cmd("generic", "conda environment management")

    def python(self, args, ctx):
        i = 0
        while i < len(args):
            a = args[i]
            if a in ("-c",) or a in ("-V", "--version", "-h", "--help"):
                return self.cmd("generic", "inline code / version")
            if a == "-m":
                return self.py_module(args[i + 1:], ctx) if i + 1 < len(args) else self.cmd("generic", "bare -m")
            if a.startswith("-m") and len(a) > 2:
                return self.py_module([a[2:]] + args[i + 1:], ctx)
            if a in ("-X", "-W", "-Q"):
                i += 2
                continue
            if a.startswith("-"):
                i += 1
                continue
            if a == "-":
                return self.cmd("generic", "reads stdin")
            return self.file_cmd(a, ctx, args[i + 1:])
        return self.cmd("generic", "interactive interpreter")

    def py_module(self, args, ctx):
        mod, rest = args[0], args[1:]
        top = mod.split(".")[0]
        if mod == "pip":
            return self.pip(rest, ctx)
        if mod in ("venv", "virtualenv"):
            self.created.update(a for a in rest if not a.startswith("-"))
            return self.cmd("generic", "creates a virtual environment")
        if mod in ("pytest", "py.test"):
            return self.pytest(rest, ctx)
        if mod in ("uvicorn", "gunicorn", "hypercorn"):
            return self.asgi(rest, ctx)
        if mod == "streamlit":
            return self.streamlit(rest, ctx)
        if mod == "pre_commit":
            return self.precommit(rest, ctx)
        path = mod.replace(".", "/")
        bases = [b for b in (ctx.cwd, self.r.readme_dir, self.r.root_rel) if b is not None]
        bases += [self.r.join(b, "src") for b in list(bases)]
        for b in bases:
            for cand in (path + ".py", path + "/__main__.py"):
                t = self.r.join(b, cand)
                if self.r.exists(t):
                    self.cmd("verified", f"{self.r.show(t)} exists")
                    return self.flags(rest, f"python -m {mod}", prefer=t)
        for b in bases:
            if self.r.exists(self.r.join(b, path + "/__init__.py")):
                return self.cmd("not_found", f"{self.r.show(self.r.join(b, path))} is a package without __main__.py")
        own = {n.replace("-", "_") for n in self.r.m["py_names"]}
        in_repo = any(self.r.exists(self.r.join(b, top)) or self.r.exists(self.r.join(b, top + ".py")) for b in bases)
        if in_repo or top in own:
            return self.cmd("not_found", f"module {mod} not found in the repo")
        if norm_pkg(top) in self.r.m["deps"]:
            return self.cmd("verified", f"{top} is a dependency")
        if mod in PY_TOOL_MODULES or top in PY_TOOL_MODULES or top in PY_STDLIB:
            return self.cmd("generic", f"{mod} is a standard/tool module")
        return self.cmd("unverifiable", f"{mod} is not part of this repo")

    def pytest(self, args, ctx):
        paths = [a.split("::")[0] for a in self.positional(args, {"-k", "-m", "-p", "-c", "--rootdir", "-n", "--maxfail", "--cov", "-o"})]
        paths = [p for p in paths if "/" in p or p.endswith(".py") or p in ("tests", "test")]
        for p in paths:
            st, ev, _ = self.locate(p, ctx)
            if st != "verified":
                return self.cmd(st, ev)
        if paths:
            return self.cmd("verified", "test paths exist")
        r = self.r
        if r.has_dep("pytest") or r.files_named("pytest.ini", "conftest.py") or \
                any(re.search(r"\[tool\.pytest|\[tool:pytest\]", read_text(r.top / f)) for f in r.files_named("pyproject.toml", "setup.cfg", "tox.ini")):
            return self.cmd("verified", "pytest is configured")
        if any(re.search(r"(^|/)test_[^/]*\.py$|_test\.py$", f) for f in r.files):
            return self.cmd("verified", "pytest-style test files exist")
        return self.cmd("unverifiable", "no pytest config or tests found")

    def precommit(self, args, ctx):
        if args[:1] in (["install"], ["run"], ["autoupdate"]) or not args:
            st, ev = self.py_manifest(ctx, (".pre-commit-config.yaml", ".pre-commit-config.yml"))
            return self.cmd(st, ev)
        return self.cmd("generic", "pre-commit housekeeping")

    def tox(self, args, ctx):
        if self.r.files_named("tox.ini") or any("[tool.tox" in read_text(self.r.top / f) for f in self.r.files_named("pyproject.toml")):
            return self.cmd("verified", "tox is configured")
        return self.cmd("not_found", "no tox.ini or [tool.tox]")

    def nox(self, args, ctx):
        if self.r.files_named("noxfile.py"):
            return self.cmd("verified", "noxfile.py exists")
        return self.cmd("not_found", "no noxfile.py")

    def module_file(self, mod, ctx):
        path = mod.replace(".", "/")
        bases = [b for b in (ctx.cwd, self.r.readme_dir, self.r.root_rel) if b is not None]
        bases += [self.r.join(b, "src") for b in list(bases)]
        for b in bases:
            for cand in (path + ".py", path + "/__init__.py"):
                t = self.r.join(b, cand)
                if self.r.exists(t):
                    return "verified", f"{self.r.show(t)} exists"
        return "not_found", f"module {mod} not found"

    def asgi(self, args, ctx):
        pos = self.positional(args, {"--host", "--port", "-b", "--bind", "-w", "--workers", "-k", "--worker-class",
                                     "--log-level", "--app-dir", "--env-file", "-c", "--config", "--timeout"})
        if not pos or ":" not in pos[0]:
            return self.cmd("unverifiable", "app target not given as module:app")
        mod = pos[0].split(":")[0]
        if is_placeholder(mod):
            return self.cmd("unverifiable", "placeholder")
        st, ev = self.module_file(mod, ctx)
        return self.cmd(st, ev)

    def streamlit(self, args, ctx):
        if args[:1] == ["run"] and len(args) > 1:
            st, ev, _ = self.locate(args[1], ctx, kinds=("file",))
            return self.cmd(st, ev)
        return self.cmd("generic", "streamlit housekeeping")

    def fastapi(self, args, ctx):
        pos = self.positional(args, {"--host", "--port", "--app"})
        if pos[:1] in (["dev"], ["run"]) and len(pos) > 1:
            st, ev, _ = self.locate(pos[1], ctx)
            return self.cmd(st, ev)
        return self.cmd("unverifiable", "fastapi CLI auto-discovers the app")

    # ---- task runners ------------------------------------------------------------
    def make(self, args, ctx):
        d, f, targets, i = None, None, [], 0
        while i < len(args):
            a = args[i]
            if a in ("-C", "--directory"):
                d = args[i + 1] if i + 1 < len(args) else None
                i += 2
                continue
            if a in ("-f", "--file", "--makefile"):
                f = args[i + 1] if i + 1 < len(args) else None
                i += 2
                continue
            if a in ("-j", "-l") and i + 1 < len(args) and args[i + 1].isdigit():
                i += 2
                continue
            if not a.startswith("-") and "=" not in a:
                targets.append(a)
            i += 1
        cands = [f] if f else ["Makefile", "makefile", "GNUmakefile"]
        mk = None
        for c in cands:
            st, ev, t = self.locate(self.r.join(d, c) if d else c, ctx, kinds=("file",))
            if st == "verified":
                mk = t
                break
            if st == "unverifiable":
                return self.cmd(st, ev, kind="script" if targets else "command")
        if mk is None:
            return self.cmd("not_found", "no Makefile", kind="script" if targets else "command")
        if not targets:
            return self.cmd("verified", f"{self.r.show(mk)} exists")
        txt = read_text(self.r.top / mk)
        defined = set()
        for line in txt.splitlines():
            mm = re.match(r"^([^\s:=#][^:=]*?)\s*::?(?!=)", line)
            if mm and not line.startswith("\t"):
                defined.update(mm.group(1).split())
        fuzzy = bool(re.search(r"^\s*-?include\s|^[^\s#]*%[^\s:]*\s*:|^\$\(", txt, re.M))
        for tname in targets:
            text = self.stmt if len(targets) == 1 else f"make {tname}"
            if tname in defined:
                self.cmd("verified", f"{self.r.show(mk)} target {tname}", kind="script", text=text)
            elif fuzzy:
                self.cmd("unverifiable", f"{self.r.show(mk)} has includes or pattern rules", kind="script", text=text)
            else:
                have = ", ".join(sorted(t for t in defined if not t.startswith("."))[:12])
                self.cmd("not_found", f"{self.r.show(mk)} has no target {tname} (targets: {have})", kind="script", text=text)

    def just(self, args, ctx):
        pos = [a for a in args if not a.startswith("-") and "=" not in a]
        if any(a in ("--list", "-l", "--summary", "--help", "--version") for a in args):
            return self.cmd("generic", "just housekeeping")
        files = [f for f in self.r.files_named("justfile", "Justfile", ".justfile")]
        if not files:
            return self.cmd("not_found", "no justfile", kind="script")
        recipes = set()
        fuzzy = False
        for f in files:
            txt = read_text(self.r.top / f)
            recipes.update(re.findall(r"^@?([A-Za-z_][\w\-]*)(?:\s+[^:=\n]*)?:(?!=)", txt, re.M))
            recipes.update(re.findall(r"^alias\s+([\w\-]+)\s*:=", txt, re.M))
            fuzzy = fuzzy or bool(re.search(r"^(import|mod)\s", txt, re.M))
        if not pos:
            return self.cmd("verified", f"{self.r.show(files[0])} exists (default recipe)", kind="script")
        name = pos[0]
        if name in recipes:
            return self.cmd("verified", f"{self.r.show(files[0])} recipe {name}", kind="script")
        if fuzzy:
            return self.cmd("unverifiable", "justfile imports other files", kind="script")
        return self.cmd("not_found", f"no recipe {name} in {self.r.show(files[0])}", kind="script")

    def task(self, args, ctx):
        files = self.r.files_named("Taskfile.yml", "Taskfile.yaml", "taskfile.yml", "taskfile.yaml", "Taskfile.dist.yml")
        pos = [a for a in args if not a.startswith("-") and "=" not in a]
        if any(a in ("--list", "-l", "--list-all", "-a", "--help", "--version", "--init") for a in args):
            return self.cmd("generic", "task housekeeping")
        if not files:
            return self.cmd("not_found" if pos else "unverifiable", "no Taskfile", kind="script")
        names = set()
        for f in files:
            names.update(yaml_children(read_text(self.r.top / f), "tasks"))
        if not pos:
            return self.cmd("verified" if "default" in names else "not_found", f"{self.r.show(files[0])} default task", kind="script")
        name = pos[0]
        if name in names or any(":" in name and n == name.split(":")[-1] for n in names):
            return self.cmd("verified", f"{self.r.show(files[0])} task {name}", kind="script")
        if any("includes" in read_text(self.r.top / f) for f in files):
            return self.cmd("unverifiable", "Taskfile includes other files", kind="script")
        return self.cmd("not_found", f"no task {name} in {self.r.show(files[0])}", kind="script")

    # ---- other ecosystems ------------------------------------------------------
    def manifest_cmd(self, names, ctx, what, patterns=False):
        """verified if one of `names` exists in the current folder, the README folder, the repo root or (lenient)
        anywhere in the repo."""
        for n in names:
            if patterns:
                for f in self.r.files:
                    if re.search(n, f.rsplit("/", 1)[-1]):
                        return self.cmd("verified", f"{self.r.show(f)} exists")
                continue
            st, ev, _ = self.locate(n, ctx, kinds=("file",))
            if st == "verified":
                return self.cmd(st, ev)
            if st == "unverifiable" and "working directory" in ev:
                if self.r.files_named(n):
                    return self.cmd("verified", f"{self.r.show(self.r.files_named(n)[0])} exists")
        for n in names:
            if not patterns and self.r.files_named(n):
                return self.cmd("verified", f"{self.r.show(self.r.files_named(n)[0])} exists")
        return self.cmd("not_found", f"no {what}")

    def cargo(self, args, ctx):
        sub = next((a for a in args if not a.startswith("-") and not a.startswith("+")), "")
        rest = args[args.index(sub) + 1:] if sub in args else []
        m = self.r.m
        if sub in ("new", "init", "search", "login", "logout", "owner", "yank", "help", "version") or not sub:
            if sub in ("new", "init"):
                self.created.update(a for a in rest if not a.startswith("-"))
            return self.cmd("generic", f"cargo {sub}".strip())
        if sub in ("add", "remove", "rm"):
            return self.cmd("generic", "edits dependencies")
        if sub == "install":
            for i, a in enumerate(rest):
                if a == "--path" and i + 1 < len(rest):
                    st, ev, t = self.locate(rest[i + 1], ctx, kinds=("dir",))
                    if st == "verified" and not self.r.exists(self.r.join(t, "Cargo.toml")):
                        return self.cmd("not_found", f"{self.r.show(t)} has no Cargo.toml")
                    return self.cmd(st, ev)
                if a == "--git" and i + 1 < len(rest):
                    if self.r.remote and normalize_remote(rest[i + 1]) == self.r.remote:
                        return self.cmd("verified", "installs this repo from git")
                    return self.cmd("unverifiable", "installs from another git repo")
            names = self.positional(rest, {"--version", "--root", "--features", "-F", "--bin", "--target"})
            if names and (names[0] in m["cargo_names"] or names[0] in m["cargo_bins"]):
                return self.cmd("verified", f"{names[0]} is this project's crate")
            return self.cmd("unverifiable", "installs a crate from crates.io")
        builtin = {"build", "b", "check", "c", "clean", "doc", "d", "run", "r", "test", "t", "bench", "update", "fmt",
                   "clippy", "fix", "tree", "vendor", "metadata", "publish", "package", "fetch"}
        if sub not in builtin:
            if not m["cargo"]:
                return self.cmd("unverifiable", f"cargo {sub} is a plugin")
            return self.cmd("unverifiable", f"cargo-{sub} is a plugin")
        if not m["cargo"]:
            return self.cmd("not_found", "no Cargo.toml")
        problems, i = [], 0
        own_args = rest
        if "--" in rest:
            own_args = rest[:rest.index("--")]
        while i < len(own_args):
            a = own_args[i]
            val = own_args[i + 1] if i + 1 < len(own_args) else ""
            key = a
            if "=" in a and a.startswith("--"):
                key, val = a.split("=", 1)
            elif a.startswith("-") and not a.startswith("--"):
                pass
            if key == "--bin" and val:
                if val not in m["cargo_bins"] and val not in m["cargo_names"]:
                    problems.append(f"no binary {val}")
            elif key == "--example" and val:
                if val not in m["cargo_examples"]:
                    problems.append(f"no example {val}")
            elif key in ("-p", "--package") and val:
                if val not in m["cargo_names"]:
                    problems.append(f"no package {val}")
            elif key in ("--features", "-F") and val:
                for feat in re.split(r"[,\s]+", val):
                    feat = feat.split("/")[-1]
                    if feat and not any(re.search(r"^\s*\"?" + re.escape(feat) + r"\"?\s*=", read_text(self.r.top / c), re.M) for c in m["cargo"]):
                        problems.append(f"no feature {feat}")
            i += 1
        if problems:
            return self.cmd("not_found", "; ".join(problems) + " in Cargo.toml")
        self.cmd("verified", f"{self.r.show(m['cargo'][0])} exists")
        if sub in ("run", "r") and "--" in rest:
            label = "cargo run"
            self.flags(rest[rest.index("--") + 1:], label)

    def go(self, args, ctx):
        sub = args[0] if args else ""
        rest = args[1:]
        if sub in ("get", "version", "env", "help", "work", "clean", "doc", "tool", "telemetry") or not sub:
            return self.cmd("generic", f"go {sub}".strip())
        gomods = self.r.files_named("go.mod")
        if sub == "mod":
            if rest[:1] == ["init"]:
                return self.cmd("generic", "creates a module")
            return self.cmd("verified", f"{self.r.show(gomods[0])} exists") if gomods else self.cmd("not_found", "no go.mod")
        if sub == "install" and rest and "@" in rest[-1] and not rest[-1].startswith("."):
            mod = (self.r.facts.get("package") or {}).get("go_module")
            target = rest[-1].split("@")[0]
            if mod and (target == mod or target.startswith(mod + "/")):
                sub_path = target[len(mod):].lstrip("/")
                st, ev, _ = self.locate(sub_path or ".", Ctx(self.r.root_rel))
                return self.cmd(st, ev)
            return self.cmd("unverifiable", "installs another module")
        if not gomods:
            return self.cmd("not_found", "no go.mod")
        value_opts = {"-o", "-tags", "-ldflags", "-gcflags", "-run", "-count", "-timeout", "-coverprofile", "-bench",
                      "-p", "-mod", "-C", "-covermode", "-coverpkg", "-exec", "-benchtime", "-parallel", "-skip"}
        i, pkgs = 0, []
        while i < len(rest):
            a = rest[i]
            if a in value_opts:
                i += 2
                continue
            if a.startswith("-"):
                i += 1
                continue
            pkgs.append((i, a))
            if sub == "run":
                break
            i += 1
        for _, p in pkgs:
            if p in (".", "./...", "...") or p.startswith("github.com") and "/" in p and not p.startswith("./"):
                continue
            pth = p[:-4] if p.endswith("/...") else p
            st, ev, _ = self.locate(pth, ctx)
            if st != "verified":
                return self.cmd(st, ev)
        self.cmd("verified", f"{self.r.show(gomods[0])} exists" + (" and the package path exists" if pkgs else ""))
        if sub == "run" and pkgs:
            self.flags(rest[pkgs[0][0] + 1:], "go run")

    def wrapper(self, prog, ctx):
        st, ev, _ = self.locate(prog, ctx, kinds=("file",))
        return self.cmd(st, ev)

    def maven(self, args, ctx):
        return self.manifest_cmd(["pom.xml"], ctx, "pom.xml")

    def gradle(self, args, ctx):
        return self.manifest_cmd(["build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts"], ctx, "build.gradle")

    def dotnet(self, args, ctx):
        sub = args[0] if args else ""
        if sub in ("new", "tool", "ef", "--version", "--info", "nuget", "workload", "dev-certs", "sdk", "--list-sdks"):
            return self.cmd("generic", f"dotnet {sub}")
        for i, a in enumerate(args):
            if a in ("--project", "-p") and i + 1 < len(args):
                st, ev, _ = self.locate(args[i + 1], ctx)
                return self.cmd(st, ev)
        return self.manifest_cmd([r"\.(csproj|fsproj|vbproj|sln|slnx)$"], ctx, "*.csproj or *.sln", patterns=True)

    def flutter(self, args, ctx):
        if args[:1] in (["create"], ["doctor"], ["upgrade"], ["channel"], ["config"], ["devices"], ["emulators"], ["--version"]):
            return self.cmd("generic", "flutter housekeeping")
        return self.manifest_cmd(["pubspec.yaml"], ctx, "pubspec.yaml")

    def mix(self, args, ctx):
        if args[:1] in (["new"], ["archive.install"], ["local.hex"], ["local.rebar"], ["phx.new"]):
            return self.cmd("generic", "mix scaffolding")
        return self.manifest_cmd(["mix.exs"], ctx, "mix.exs")

    def bundle(self, args, ctx):
        if args[:1] == ["exec"] and len(args) > 1:
            self.manifest_cmd(["Gemfile"], ctx, "Gemfile")
            return
        return self.manifest_cmd(["Gemfile"], ctx, "Gemfile")

    def rails(self, args, ctx):
        if args[:1] == ["new"]:
            return self.cmd("generic", "scaffolds a new app")
        if self.r.files_named("Gemfile") and "rails" in read_text(self.r.top / self.r.files_named("Gemfile")[0]):
            return self.cmd("verified", "Gemfile depends on rails")
        if self.r.files_named("Rakefile"):
            return self.cmd("verified", "Rakefile exists")
        return self.cmd("not_found", "no Rails Gemfile or Rakefile")

    def composer(self, args, ctx):
        sub = args[0] if args else "install"
        if sub in ("require", "create-project", "global", "self-update", "--version", "diagnose"):
            return self.cmd("generic", f"composer {sub}")
        if sub in ("run", "run-script") and len(args) > 1:
            for f in self.r.files_named("composer.json"):
                scripts = (load_json(self.r.top / f) or {}).get("scripts") or {}
                if args[1] in scripts:
                    return self.cmd("verified", f"{self.r.show(f)} scripts.{args[1]}", kind="script")
            return self.cmd("not_found", f"no composer script {args[1]}", kind="script")
        return self.manifest_cmd(["composer.json"], ctx, "composer.json")

    def php(self, args, ctx):
        pos = self.positional(args, {"-S", "-t", "-d", "-c"})
        if not pos or "-S" in args or "-r" in args:
            return self.cmd("generic", "php built-in")
        st, ev, _ = self.locate(pos[0], ctx, kinds=("file",))
        return self.cmd(st, ev)

    def swift(self, args, ctx):
        if args[:1] in (["build"], ["run"], ["test"], ["package"]):
            return self.manifest_cmd(["Package.swift"], ctx, "Package.swift")
        return self.cmd("generic", "swift")

    def zig(self, args, ctx):
        if args[:1] == ["build"]:
            return self.manifest_cmd(["build.zig"], ctx, "build.zig")
        if args[:1] in (["run"], ["test"]) and len(args) > 1:
            st, ev, _ = self.locate(args[1], ctx, kinds=("file",))
            return self.cmd(st, ev)
        return self.cmd("generic", "zig")

    def stack(self, args, ctx):
        if args[:1] in (["new"], ["setup"], ["upgrade"]):
            return self.cmd("generic", "stack housekeeping")
        return self.manifest_cmd(["stack.yaml"], ctx, "stack.yaml")

    def cabal(self, args, ctx):
        if args[:1] in (["update"], ["init"]):
            return self.cmd("generic", "cabal housekeeping")
        return self.manifest_cmd([r"\.cabal$|^cabal\.project$"], ctx, "*.cabal", patterns=True)

    def cmake(self, args, ctx):
        for i, a in enumerate(args):
            if a == "-S" and i + 1 < len(args):
                st, ev, t = self.locate(args[i + 1], ctx, kinds=("dir",))
                if st == "verified" and not self.r.exists(self.r.join(t, "CMakeLists.txt")):
                    return self.cmd("not_found", f"{self.r.show(t)} has no CMakeLists.txt")
                return self.cmd(st, ev)
        return self.manifest_cmd(["CMakeLists.txt"], ctx, "CMakeLists.txt")

    def meson(self, args, ctx):
        return self.manifest_cmd(["meson.build"], ctx, "meson.build")

    def terraform(self, args, ctx):
        if any(f.endswith(".tf") for f in self.r.files):
            return self.cmd("verified", "Terraform files exist")
        return self.cmd("unverifiable", "no *.tf files found")

    def kubectl(self, args, ctx):
        for i, a in enumerate(args):
            if a in ("-f", "--filename", "-k", "--kustomize") and i + 1 < len(args):
                if args[i + 1].startswith(("http://", "https://")):
                    return self.cmd("generic", "remote manifest")
                st, ev, _ = self.locate(args[i + 1], ctx)
                return self.cmd(st, ev)
        return self.cmd("generic", "cluster operation")

    def helm(self, args, ctx):
        pos = self.positional(args, {"-f", "--values", "-n", "--namespace", "--set", "--version", "--repo"})
        if args[:1] in (["install"], ["upgrade"], ["template"]) and len(pos) >= 3 and pos[2].startswith(("./", "../")):
            st, ev, _ = self.locate(pos[2], ctx, kinds=("dir",))
            return self.cmd(st, ev)
        return self.cmd("generic", "helm operation")

    def devtool(self, base, args):
        if self.r.has_dep(*DEV_TOOLS[base]):
            return self.cmd("verified", f"{base} is a dependency")
        return self.cmd("unverifiable", f"{base} is not a declared dependency")

    # ---- docker ------------------------------------------------------------------
    def compose_files(self, ctx, explicit):
        if explicit:
            out = []
            for f in explicit:
                st, ev, t = self.locate(f, ctx, kinds=("file",))
                if st != "verified":
                    return None, (st, ev)
                out.append(t)
            return out, None
        names = ("compose.yaml", "compose.yml", "docker-compose.yaml", "docker-compose.yml")
        for b in (ctx.cwd, self.r.readme_dir, self.r.root_rel):
            if b is None:
                continue
            found = [self.r.join(b, n) for n in names if self.r.exists(self.r.join(b, n))]
            if found:
                for f in self.r.files:
                    name = f.rsplit("/", 1)[-1]
                    if f.rsplit("/", 1)[0] == (f.rsplit("/", 1)[0] if "/" in f else "") and \
                            re.match(r"^(docker-)?compose\.[\w.\-]+\.ya?ml$", name) and (f.rsplit("/", 1)[0] if "/" in f else "") == b:
                        found.append(f)
                return found, None
        anywhere = [f for f in self.r.files if re.match(r"^(docker-)?compose(\.[\w\-]+)?\.ya?ml$", f.rsplit("/", 1)[-1])]
        if anywhere:
            return None, ("unverifiable", f"compose file only at {self.r.show(anywhere[0])}")
        if ctx.cwd is None:
            return None, ("unverifiable", "working directory unknown")
        return None, ("not_found", "no compose.yaml / docker-compose.yml")

    def docker(self, args, ctx):
        if not args:
            return self.cmd("generic", "bare docker")
        if args[0] == "compose":
            return self.compose(args[1:], ctx)
        if args[0] == "buildx" and args[1:2] == ["build"]:
            args = args[1:]
        sub = args[0]
        if sub == "build":
            return self.docker_build(args[1:], ctx)
        if sub == "run":
            pos = self.positional(args[1:], {"-p", "--publish", "-e", "--env", "-v", "--volume", "--name", "-w",
                                             "--workdir", "--env-file", "--network", "--entrypoint", "-u", "--user",
                                             "--platform", "--mount", "--gpus", "-m", "--memory", "--restart", "-l"})
            if pos and pos[0] in self.built_tags:
                return self.cmd("verified", f"image {pos[0]} is built above")
            return self.cmd("unverifiable", "runs an image")
        return self.cmd("generic", f"docker {sub}")

    def docker_build(self, args, ctx):
        dockerfile, context, i = None, None, 0
        while i < len(args):
            a = args[i]
            if a in ("-f", "--file"):
                dockerfile = args[i + 1] if i + 1 < len(args) else None
                i += 2
                continue
            if a in ("-t", "--tag"):
                if i + 1 < len(args):
                    self.built_tags.add(args[i + 1])
                    self.built_tags.add(args[i + 1].split(":")[0])
                i += 2
                continue
            if a in ("--build-arg", "--target", "--platform", "--secret", "--cache-from", "--label", "--network",
                     "--progress", "--ssh", "-o", "--output"):
                i += 2
                continue
            if not a.startswith("-"):
                context = a
            i += 1
        if context and re.match(r"^(https?|git)[:@]", context):
            return self.cmd("generic", "remote build context")
        if context in (None, "-"):
            context = "."
        st, ev, t = self.locate(context, ctx, kinds=("dir",))
        if st != "verified":
            return self.cmd(st, ev)
        if dockerfile:
            st, ev, _ = self.locate(dockerfile, ctx, kinds=("file",))
            return self.cmd(st, ev)
        df = self.r.join(t, "Dockerfile")
        if self.r.exists(df):
            return self.cmd("verified", f"{self.r.show(df)} exists")
        return self.cmd("not_found", f"no Dockerfile in {self.r.show(t)}")

    def compose(self, args, ctx):
        files, i, sub, rest = [], 0, None, []
        while i < len(args):
            a = args[i]
            if a in ("-f", "--file"):
                if i + 1 < len(args):
                    files.append(args[i + 1])
                i += 2
                continue
            if a in ("-p", "--project-name", "--profile", "--env-file", "--project-directory", "--ansi", "--progress"):
                i += 2
                continue
            if a.startswith("-"):
                i += 1
                continue
            sub, rest = a, args[i + 1:]
            break
        if sub in ("version", "ls", "--version") or sub is None:
            return self.cmd("generic", "docker compose housekeeping")
        found, err = self.compose_files(ctx, files)
        if err:
            return self.cmd(*err)
        services = set()
        for f in found:
            services.update(yaml_children(read_text(self.r.top / f), "services"))
        value_opts = {"--scale", "-t", "--timeout", "--exit-code-from", "--attach", "--no-attach", "-e", "--env",
                      "--name", "-u", "--user", "-v", "--volume", "-w", "--workdir", "--entrypoint", "-l", "--label",
                      "--index", "--pull", "--wait-timeout", "-p", "--publish", "--tail", "--since", "--until", "-n",
                      "--signal", "-s"}
        pos = self.positional(rest, value_opts)
        if sub in ("run", "exec"):
            pos = pos[:1]
        elif sub not in ("up", "start", "stop", "restart", "build", "pull", "push", "logs", "create", "rm", "kill",
                         "down", "ps", "top", "pause", "unpause", "watch", "port", "events", "images", "config"):
            pos = []
        if sub in ("down", "config", "ps", "top", "images", "port", "events"):
            pos = [] if sub != "ps" else pos
        shown = ", ".join(self.r.show(f) for f in found)
        missing = [s for s in pos if s not in services]
        if missing:
            if not services:
                return self.cmd("unverifiable", f"could not read services from {shown}")
            return self.cmd("not_found", f"no service {', '.join(missing)} in {shown} (services: {', '.join(sorted(services))})")
        return self.cmd("verified", f"{shown}" + (f" defines {', '.join(pos)}" if pos else " exists"))

    # ---- git / filesystem -----------------------------------------------------------
    def git(self, args, ctx):
        if args[:1] != ["clone"]:
            return self.cmd("generic", f"git {args[0] if args else ''}".strip())
        pos = self.positional(args[1:], {"-b", "--branch", "--depth", "-o", "--origin", "--filter", "--reference", "-c", "--config", "-j", "--jobs"})
        if not pos:
            return self.cmd("generic", "git clone")
        url = pos[0]
        dest = pos[1] if len(pos) > 1 else re.sub(r"\.git$", "", url.rstrip("/").rsplit("/", 1)[-1].rsplit(":", 1)[-1])
        self.created.add(dest)
        if is_placeholder(url):
            self.clone_dirs.add(dest)
            return self.cmd("unverifiable", "placeholder URL")
        n = normalize_remote(url)
        if self.r.remote and n == self.r.remote:
            self.clone_dirs.add(dest)
            return self.cmd("verified", "matches the origin remote")
        base = n.rsplit("/", 1)[-1]
        if base.lower() in self.r.repo_names:
            self.clone_dirs.add(dest)
        if not self.r.remote:
            return self.cmd("unverifiable", "repo has no origin remote to compare")
        return self.cmd("unverifiable", f"origin is {self.r.remote}")

    def cd(self, args, ctx):
        pos = [a for a in args if not a.startswith("-") or a == "-"]
        if not pos or pos[0] in ("~", "-", "$HOME", "%USERPROFILE%"):
            ctx.cwd = None if pos and pos[0] != "-" else ctx.cwd
            return self.cmd("generic", "changes to the home/previous directory")
        p = pos[0].strip("'\"").replace("\\", "/").rstrip("/") or "/"
        if set(p.split("/")) <= {"..", "."}:
            if ctx.cwd is not None:
                t = self.r.join(ctx.cwd, p)
                ctx.cwd = t if not t.startswith("..") else None
            return self.cmd("generic", "moves up a directory")
        if p.startswith(("~", "/", "$", "%")) or re.match(r"^[A-Za-z]:/", p):
            ctx.cwd = None
            return self.cmd("generic", "directory outside the repository")
        first = p.split("/", 1)[0]
        if first in self.clone_dirs or (first.lower() in self.r.repo_names and (ctx.cwd is None or not self.r.exists(self.r.join(ctx.cwd, first)))):
            rest = p.split("/", 1)[1] if "/" in p else ""
            if not rest:
                ctx.cwd = ""
                return self.cmd("verified", "the repository folder (after git clone)")
            if self.r.is_dir(rest):
                ctx.cwd = rest
                return self.cmd("verified", f"{self.r.show(rest)} exists in the cloned repo")
            ctx.cwd = None
            return self.cmd("not_found", f"no folder {rest} in the repo")
        st, ev, t = self.locate(p, ctx, kinds=("dir",))
        if st == "verified" and t is not None and self.r.is_dir(t):
            ctx.cwd = t
            return self.cmd("verified", f"{self.r.show(t)}/ exists")
        ctx.cwd = None
        if st == "verified":
            return self.cmd("not_found", f"{p} is a file, not a folder")
        return self.cmd(st, ev)

    def copy(self, args, ctx):
        pos = self.positional(args, {"-t", "--target-directory", "-Destination", "-Path"})
        if not pos:
            return self.cmd("generic", "copy")
        st, ev, _ = self.locate(pos[0], ctx)
        if len(pos) > 1:
            self.created.add(pos[-1].strip("/"))
        return self.cmd(st, ev)

    def run_file(self, prog, args, ctx):
        p = prog.replace("\\", "/")
        name = p.rsplit("/", 1)[-1]
        st, ev, t = self.locate(p, ctx, kinds=("file",))
        if st == "unverifiable" and ev == "build output":
            bins = self.r.m["bins"]
            stem = os.path.splitext(name)[0]
            if stem in bins or stem in self.r.m["cargo_names"]:
                self.cmd("verified", f"build output of binary {stem}")
                return self.flags(args, stem)
            return self.cmd(st, ev)
        self.cmd(st, ev)
        if st == "verified":
            self.flags(args, name, prefer=t)

    def file_cmd(self, p, ctx, rest):
        if is_placeholder(p):
            return self.cmd("unverifiable", "placeholder")
        st, ev, t = self.locate(p, ctx)
        self.cmd(st, ev)
        if st == "verified":
            self.flags(rest, p.rsplit("/", 1)[-1], prefer=t)

    def shell(self, args, ctx):
        i = 0
        while i < len(args):
            a = args[i]
            if a.lower() in ("-c", "-command", "-encodedcommand"):
                return self.cmd("generic", "inline shell code")
            if a.lower() in ("-file", "-f"):
                if i + 1 < len(args):
                    return self.file_cmd(args[i + 1], ctx, args[i + 2:])
            if a.lower() in ("-executionpolicy",):
                i += 2
                continue
            if a.startswith("-"):
                i += 1
                continue
            return self.file_cmd(a, ctx, args[i + 1:])
        return self.cmd("generic", "interactive shell")

    def node(self, args, ctx):
        i = 0
        while i < len(args):
            a = args[i]
            if a in ("-e", "--eval", "-p", "--print", "-v", "--version", "-h", "--help", "--test", "-i"):
                return self.cmd("generic", "node built-in")
            if a in ("-r", "--require", "--import", "--loader", "--env-file", "--inspect-port", "-C", "--conditions"):
                i += 2
                continue
            if a.startswith("-"):
                i += 1
                continue
            return self.file_cmd(a, ctx, args[i + 1:])
        return self.cmd("generic", "node REPL")

    def deno(self, args, ctx):
        sub = args[0] if args else ""
        if sub == "task":
            pos = self.positional(args[1:], {"--cwd", "-c", "--config"})
            if not pos:
                return self.cmd("generic", "lists tasks")
            for f in self.r.files_named("deno.json", "deno.jsonc", "package.json"):
                if re.search(r"\"" + re.escape(pos[0]) + r"\"\s*:", read_text(self.r.top / f)):
                    return self.cmd("verified", f"{self.r.show(f)} task {pos[0]}", kind="script")
            return self.cmd("not_found", f"no deno task {pos[0]}", kind="script")
        if sub in ("run", "serve", "test", "bench", "compile", "check") or (sub and not sub.startswith("-") and os.path.splitext(sub)[1]):
            pos = [a for a in (args[1:] if sub in ("run", "serve", "test", "bench", "compile", "check") else args) if not a.startswith("-")]
            if not pos:
                return self.cmd("generic", f"deno {sub}")
            if pos[0].startswith(("http://", "https://", "jsr:", "npm:")):
                return self.cmd("unverifiable", "remote module")
            return self.file_cmd(pos[0], ctx, args[args.index(pos[0]) + 1:])
        return self.cmd("generic", f"deno {sub}".strip())


def yaml_children(text: str, key: str):
    """Child keys of a top-level YAML mapping (services:, tasks:)."""
    m = re.search(r"^" + re.escape(key) + r":[ \t]*(?:#.*)?\n((?:[ \t]+.*\n?|[ \t]*\n)+)", text, re.M)
    out = []
    if not m:
        return out
    indent = None
    for line in m.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        mm = re.match(r"^([ \t]+)[\"']?([\w\-.:]+)[\"']?:\s*(?:#.*|\{\}|&\w+)?$", line) or \
            re.match(r"^([ \t]+)[\"']?([\w\-.:]+)[\"']?:\s*\S", line)
        if mm:
            if indent is None:
                indent = mm.group(1)
            if mm.group(1) == indent:
                out.append(mm.group(2))
    return out


# --------------------------------------------------------------------------- extraction
def logical_lines(block_lines, lang):
    """Yield (lineno, command text) for a fenced block, applying prompt/continuation/heredoc rules."""
    texts = [t for _, t in block_lines]
    if any(ch in "".join(texts) for ch in "├└│"):
        return []
    ps = lang in PS_LANGS
    prompted = prompt_lines(texts)
    any_prompt = any(prompted)
    out, i, n = [], 0, len(block_lines)
    while i < n:
        lineno, t = block_lines[i]
        if any_prompt:
            if not prompted[i]:
                i += 1
                continue
            t = PROMPT.sub("", t, count=1)
        if ps or re.search(r"(^|\s)\.\\\w", t):
            t = t.replace("\\", "/") if not t.rstrip().endswith("`") else t
        stripped = t.strip()
        if not stripped or stripped.startswith(("#", "//", "REM ", "rem ", "::")):
            i += 1
            continue
        # continuations: trailing \ (sh), ` (PowerShell), ^ (cmd); unbalanced quotes
        while i + 1 < n:
            s = t.rstrip()
            cont = s.endswith("\\") or (s.endswith("`") and ps) or (s.endswith("^") and lang in ("cmd", "bat", "batch"))
            unbalanced = False
            if not cont:
                try:
                    shlex.split(re.split(r"(?<=\s)#", t)[0] if "#" in t else t)
                except ValueError:
                    unbalanced = True
            if not cont and not unbalanced:
                break
            nxt = block_lines[i + 1][1]
            if any_prompt:
                nxt = re.sub(r"^\s*>\s?", "", nxt)
            t = (s[:-1].rstrip() if cont else s) + (" " if cont else "\n") + nxt.strip()
            i += 1
            if unbalanced and t.count("\n") > 40:
                break
        heredoc = re.search(r"<<-?\s*['\"]?(\w+)['\"]?", t)
        out.append((lineno, t.replace("\n", " ")))
        i += 1
        if heredoc:
            end = heredoc.group(1)
            while i < n and block_lines[i][1].strip() != end:
                i += 1
            i += 1
    return out


def first_word(s: str) -> str:
    w = s.strip().split(None, 1)[0] if s.strip() else ""
    w = w.replace("\\", "/")
    base = w.lower().rsplit("/", 1)[-1] if not w.startswith(("./", "../")) else w.lower()
    if base.endswith(".exe"):
        base = base[:-4]
    if re.fullmatch(r"python(\d+(\.\d+)?)?|py", base):
        return "python"
    if re.fullmatch(r"pip\d+(\.\d+)?", base):
        return "pip"
    return base


def looks_like_command(s: str, bins) -> bool:
    words = s.strip().split()
    if len(words) < 2:
        return False
    w = first_word(s)
    while w in ("sudo",) and len(words) > 2:
        words = words[1:]
        w = first_word(" ".join(words))
    return w in INLINE_TOOLS or words[0] in bins or words[0].startswith(("./", ".\\")) or \
        bool(re.match(r"^[A-Z][A-Z0-9_]*=\S+\s+\S", s))


def table_is_env(header: str) -> bool:
    h = header.lower()
    return "variable" in h or re.search(r"\benv\b|environment", h) is not None or ("name" in h and "default" in h)


def env_from_code(text):
    """(name, offset) pairs for env var usages in a code block."""
    pats = [
        (re.compile(r"(?:^|[\s;&|(])(?:export\s+|set\s+|setx\s+|ENV\s+|ARG\s+)?([A-Z][A-Z0-9_]*)=(?!=)", re.M), True),
        (re.compile(r"\bexport\s+([A-Z][A-Z0-9_]*)\b"), True),
        (re.compile(r"\$env:([A-Z][A-Z0-9_]*)\b"), True),
        (re.compile(r"\$\{([A-Z][A-Z0-9_]*)(?:[:?\-=+][^}]*)?\}"), True),
        (re.compile(r"\$([A-Z][A-Z0-9_]*)\b"), True),
        (re.compile(r"%([A-Z][A-Z0-9_]*)%"), True),
    ] + [(p, True) for p in ENV_PATTERNS]
    out = []
    for rx, _ in pats:
        for m in rx.finditer(text):
            out.append((m.group(1), m.start(1)))
    return out


def extract(text: str, repo: Repo, v: Verifier):
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks, in_code = parse_fences(lines)
    lines = blank_html_comments(lines, in_code)
    bins = repo.m["bins"]
    env_hits = []  # (name, line, context)

    # ---- fenced code: commands + env vars ---------------------------------------
    for b in blocks:
        lang = b["lang"]
        btext_lines = [(ln, lines[ln - 1]) for ln, _ in b["lines"]]
        if lang != "mermaid":
            for ln, t in btext_lines:
                for name, _ in env_from_code(t):
                    env_hits.append((name, ln, "code"))
        if lang not in STRICT_LANGS and lang not in LOOSE_LANGS:
            continue
        strict = lang in STRICT_LANGS
        ctx = Ctx(repo.readme_dir)
        any_prompt = any(prompt_lines([t for _, t in btext_lines]))
        for ln, logical in logical_lines(btext_lines, lang):
            if not strict and not any_prompt:
                fw = first_word(logical)
                if fw not in KNOWN_TOOLS and fw not in GENERIC_PROGRAMS and logical.split()[0] not in bins \
                        and not logical.strip().startswith(("./", ".\\")) and not re.match(r"^[A-Z][A-Z0-9_]*=", logical.strip()):
                    continue
            for stmt in split_statements(logical):
                v.command(stmt, ctx, ln)

    # ---- prose: inline code, links, tables, sections ----------------------------
    section_env, section_level = False, 0
    table_env, in_table = False, False
    for idx, line in enumerate(lines):
        ln = idx + 1
        if in_code[idx]:
            in_table = False
            continue
        hm = re.match(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$", line) or re.match(r"^\s*<h([1-6])[^>]*>(.*?)</h\1>", line, re.I)
        if hm:
            level = len(hm.group(1)) if hm.group(1).startswith("#") else int(hm.group(1))
            title = re.sub(r"<[^>]+>", "", hm.group(2)).lower()
            if section_env and level <= section_level:
                section_env = False
            if re.search(r"config|environment", title):
                section_env, section_level = True, level
        # tables
        if "|" in line:
            nxt = lines[idx + 1] if idx + 1 < len(lines) else ""
            if not in_table and re.match(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$", nxt):
                in_table, table_env = True, table_is_env(line)
                continue
        else:
            in_table = False
        spans = [(m.group(2).strip(), m.start()) for m in re.finditer(r"(`+)(?!`)(.+?)(?<!`)\1(?!`)", line)]
        cells = None
        if in_table and table_env:
            cells = [c for c in line.strip().strip("|").split("|")]
        for span, pos in spans:
            if not span:
                continue
            # env vars
            em = re.match(r"^(?:export\s+|set\s+|\$env:|\$)?\{?([A-Z][A-Z0-9_]*)\}?(?:=.*)?$", span)
            if em:
                name = em.group(1)
                first_cell = cells is not None and cells and ("`" + span + "`") in cells[0]
                if ENV_NAME.match(name):
                    if (in_table and table_env) or section_env or "=" in span or span.startswith(("export ", "$")):
                        env_hits.append((name, ln, "prose"))
                    continue
                if ENV_WORD.match(name) and (first_cell or "=" in span or span.startswith(("export ", "$env:"))):
                    env_hits.append((name, ln, "prose"))
                    continue
            if looks_like_command(span, bins):
                ctx = Ctx(repo.readme_dir)
                for stmt in split_statements(span):
                    v.command(stmt, ctx, ln)
                continue
            inline_path(span, ln, repo, v)
        # links (with inline code blanked)
        no_code = re.sub(r"(`+)(?!`)(.+?)(?<!`)\1(?!`)", lambda m: " " * len(m.group(0)), line)
        targets = [m.group(1) for m in re.finditer(r"\]\(\s*<?([^)\s>]+)>?(?:\s+[\"'(][^)]*)?\)", no_code)]
        mm = re.match(r"^\s{0,3}\[[^\]]+\]:\s*<?(\S+?)>?(?:\s|$)", no_code)
        if mm:
            targets.append(mm.group(1))
        for m in re.finditer(r"\b(src|href|srcset)\s*=\s*[\"']([^\"']+)[\"']", no_code, re.I):
            if m.group(1).lower() == "srcset":
                targets += [c.strip().split()[0] for c in m.group(2).split(",") if c.strip()]
            else:
                targets.append(m.group(2))
        for tgt in targets:
            link_path(tgt, ln, repo, v)

    # ---- env var claims -----------------------------------------------------------
    seen = set()
    for name, ln, _ in sorted(env_hits, key=lambda x: x[1]):
        if name in seen or name in ENV_EXCLUDE or len(name) < 2:
            continue
        seen.add(name)
        if not ENV_NAME.match(name) and not ENV_WORD.match(name):
            continue
        v.line = ln
        check_env(name, ln, repo, v)


def check_env(name, ln, repo: Repo, v: Verifier):
    if name in ENV_GENERIC or name.startswith(ENV_GENERIC_PREFIX):
        return v.add("env_var", name, "generic", "set by the shell/OS/CI platform", line=ln)
    f = repo.grep(re.compile(r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])"))
    if f:
        return v.add("env_var", name, "verified", f"used in {repo.show(f)}", line=ln)
    sdks = IMPLICIT_ENV.get(name)
    if sdks and repo.has_dep(*sdks):
        return v.add("env_var", name, "verified", f"read implicitly by the {sdks[0]} SDK (a dependency)", line=ln)
    low = name.lower()
    for path, text, src in repo.corpus:
        if not src:
            continue
        if path.endswith(".py") and "BaseSettings" in text:
            pref = re.search(r"env_prefix\s*=\s*['\"]([A-Za-z0-9_]*)['\"]", text)
            p = (pref.group(1).lower() if pref else "")
            if low.startswith(p) and re.search(r"^\s+" + re.escape(low[len(p):]) + r"\s*:", text, re.M):
                return v.add("env_var", name, "verified", f"pydantic-settings field in {repo.show(path)}", line=ln)
        if path.endswith(".rs") and re.search(r"\benv\b", text) and re.search(r"\b" + re.escape(low) + r"\s*:", text) and "clap" in text:
            return v.add("env_var", name, "verified", f"clap env field in {repo.show(path)}", line=ln)
        if path.endswith(".go") and "AutomaticEnv" in text:
            pref = re.search(r"SetEnvPrefix\(\s*\"(\w+)\"", text)
            key = low[len(pref.group(1)) + 1:] if pref and low.startswith(pref.group(1).lower() + "_") else low
            if re.search(r"\"" + re.escape(key).replace("_", "[._]") + r"\"", text):
                return v.add("env_var", name, "verified", f"viper key in {repo.show(path)}", line=ln)
    return v.add("env_var", name, "not_found", "not referenced in any code, config or .env file", line=ln)


def clean_target(t: str):
    t = t.strip().strip("'\"")
    t = t.split("#", 1)[0].split("?", 1)[0]
    return unquote(t)


def link_path(target, ln, repo: Repo, v: Verifier):
    raw = target.strip()
    if not raw or raw.startswith(("#", "//")) or re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:", raw):
        return
    if is_placeholder(raw) or GITHUB_ROUTE.match(raw):
        return
    p = clean_target(raw)
    if not p:
        return
    if p.startswith("/"):
        t = repo.join(repo.root_rel, p.lstrip("/"))
    else:
        t = repo.join(repo.readme_dir, p)
    ex = repo.exists(t)
    shown = raw.split("#", 1)[0].split("?", 1)[0]
    if ex is None:
        return v.add("path", shown, "unverifiable", "points outside the repository", line=ln)
    if ex:
        return v.add("path", shown, "verified", f"{repo.show(t)} exists", line=ln)
    if (repo.top / t).exists():
        return v.add("path", shown, "not_found", f"case mismatch: {repo.show(t)} differs in letter case on disk", line=ln)
    return v.add("path", shown, "not_found", f"no {repo.show(t)} in the repo", line=ln)


def inline_path(span, ln, repo: Repo, v: Verifier):
    s = span.strip().strip("'\"")
    if not s or re.search(r"\s", s) or "://" in s or s.startswith(("www.", "-", "/", "~", "@", "$", "%", "#", "!", "+")):
        return
    if re.search(r"[*?\[\]<>{}=:,;|()@&^\\]", s) or is_placeholder(s) or s.startswith(".."):
        if not (s.startswith("../") and not re.search(r"[*?\[\]<>{}=:,;|()@&^\\]", s)):
            return
    name = s.rstrip("/").rsplit("/", 1)[-1]
    ext = os.path.splitext(name)[1].lower()
    has_ext = ext in PATH_EXT or name in PATH_NAMES
    if "/" not in s and not has_ext:
        return
    if re.fullmatch(r"v?\d+(\.\d+)+", s) or re.fullmatch(r"[A-Z][\w]*\.js", s) and not repo.by_name.get(s):
        return
    p = s.rstrip("/")
    for b in (repo.readme_dir, repo.root_rel, ""):
        t = repo.join(b, p)
        if repo.exists(t):
            return v.add("path", s, "verified", f"{repo.show(t)} exists", line=ln)
    if "/" not in p and s.endswith("/"):
        hit = repo.suffix_match(p)
        if hit and repo.is_dir(hit):
            return v.add("path", s, "verified", f"found at {repo.show(hit)}/", line=ln)
        return v.add("path", s, "unverifiable", "folder not found in the repo (may be created by the user)", line=ln)
    if "/" not in p:
        if repo.by_name.get(p):
            return v.add("path", s, "verified", f"found at {repo.show(repo.by_name[p][0])}", line=ln)
        return v.add("path", s, "unverifiable", "file name not found in the repo (may be created by the user)", line=ln)
    hit = repo.suffix_match(p)
    if hit:
        return v.add("path", s, "verified", f"found at {repo.show(hit)}", line=ln)
    first = p.split("/", 1)[0]
    known = repo.is_dir(repo.join(repo.readme_dir, first)) or repo.is_dir(repo.join(repo.root_rel, first))
    if first in BUILD_DIRS:
        return v.add("path", s, "unverifiable", "build output", line=ln)
    if known or first in COMMON_DIRS:
        return v.add("path", s, "not_found", f"no {p} in the repo", line=ln)
    if has_ext or s.endswith("/"):
        return v.add("path", s, "unverifiable", f"'{first}/' is not a folder in this repo", line=ln)
    return None


# --------------------------------------------------------------------------- report
def verify(readme: Path, repo_path: Path) -> dict:
    text = readme.read_text(encoding="utf-8", errors="ignore")
    repo = Repo(repo_path, readme)
    v = Verifier(repo)
    extract(text, repo, v)
    claims = sorted(v.claims, key=lambda c: (c["line"], KINDS.index(c["kind"]) if c["kind"] in KINDS else 9))
    summary = {s: sum(1 for c in claims if c["status"] == s) for s in STATUSES}
    summary["checked"] = summary["verified"] + summary["not_found"]
    summary["accuracy"] = round(100 * summary["verified"] / summary["checked"], 1) if summary["checked"] else None
    by_kind = {}
    for c in claims:
        if c["status"] == "generic":
            continue
        k = by_kind.setdefault(c["kind"], {"verified": 0, "not_found": 0, "unverifiable": 0})
        k[c["status"]] += 1
    return {"readme": str(readme), "repo": str(repo_path), "summary": summary, "by_kind": by_kind, "claims": claims}


def summary_line(s: dict) -> str:
    acc = f"{s['accuracy']}%" if s["accuracy"] is not None else "n/a"
    return (f"claims: {s['checked']} checked · {s['verified']} verified · {s['not_found']} not found · "
            f"{s['unverifiable']} unverifiable · {s['generic']} generic · accuracy {acc}")


def main(argv):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = list(argv[1:])
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    readme, repo, as_json, min_acc = None, None, False, None
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--json":
            as_json = True
        elif a in ("--repo", "--min-accuracy"):
            if i + 1 >= len(args):
                print(f"error: {a} needs a value", file=sys.stderr)
                return 2
            if a == "--repo":
                repo = Path(args[i + 1])
            else:
                try:
                    min_acc = float(args[i + 1])
                except ValueError:
                    print(f"error: --min-accuracy expects a number, got {args[i + 1]!r}", file=sys.stderr)
                    return 2
            i += 1
        elif a.startswith("-"):
            print(f"error: unknown option {a}", file=sys.stderr)
            return 2
        elif readme is None:
            readme = Path(a)
        else:
            print(f"error: unexpected argument {a}", file=sys.stderr)
            return 2
        i += 1
    if readme is None or not readme.is_file():
        print(f"error: {readme} not found", file=sys.stderr)
        return 2
    repo = repo if repo is not None else readme.resolve().parent
    if not repo.is_dir():
        print(f"error: {repo} is not a directory", file=sys.stderr)
        return 2
    report = verify(readme, repo)
    s = report["summary"]
    if as_json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for c in report["claims"]:
            if c["status"] == "generic":
                continue
            print(f"{SYMBOL[c['status']]} {c['line']:>4}  {c['kind']:<15} {c['text']}  [{c['evidence']}]")
        print(summary_line(s))
    if min_acc is not None and s["accuracy"] is not None and s["accuracy"] < min_acc:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
