"""Fixture-backed tests for readme-forge/scripts/analyze_repo.py.

Every ecosystem the README claims is backed by an on-disk fixture under
tests/fixtures/ecosystems/<name>/ and asserted here. Run from the repo root:

    python -m unittest discover -s tests -v
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "readme-forge" / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "ecosystems"
sys.path.insert(0, str(SCRIPTS))

import analyze_repo  # noqa: E402

# Distinct language/toolchain families only: npm, pnpm, Yarn and Bun are ONE ecosystem.
# Display name -> fixture dirs that prove it. The README's "N+ ecosystems" claim is len(ECOSYSTEMS).
ECOSYSTEMS = {
    "Node.js (npm, pnpm, Yarn, Bun)": ["node-npm", "node-pnpm", "node-yarn", "node-bun"],
    "Python (pip, uv, Poetry, PDM, Hatch, Pipenv, conda, setup.py)": [
        "python-pip-requirements", "python-uv", "python-poetry", "python-pdm", "python-hatch",
        "python-pipenv", "python-conda", "python-setup-py"],
    "Rust (Cargo)": ["rust"],
    "Go (modules)": ["go"],
    "JVM: Java/Kotlin (Maven, Gradle, Android)": ["maven", "gradle", "gradle-android"],
    "Ruby (Bundler, Rails)": ["ruby-rails"],
    "PHP (Composer, Laravel)": ["php-laravel"],
    "Dart (Flutter)": ["flutter"],
    "Elixir (Mix, Phoenix)": ["elixir-phoenix"],
    ".NET (csproj/sln)": ["dotnet"],
    "C/C++ (CMake)": ["cmake"],
    "Deno": ["deno"],
    "Swift (Swift Package Manager)": ["swift"],
    "Zig": ["zig"],
    "Haskell (Stack, Cabal)": ["haskell-stack", "haskell-cabal"],
}

_CACHE = {}


def facts(name):
    if name not in _CACHE:
        _CACHE[name] = analyze_repo.analyze(FIXTURES / name)
    return _CACHE[name]


class EcosystemClaimTest(unittest.TestCase):
    def test_ecosystem_count(self):
        # Keeps the README's "15+ ecosystems" honest: lower this and the README must change too.
        self.assertGreaterEqual(len(ECOSYSTEMS), 15)

    def test_every_ecosystem_fixture_is_detected(self):
        for eco, dirs in ECOSYSTEMS.items():
            for d in dirs:
                with self.subTest(ecosystem=eco, fixture=d):
                    self.assertTrue((FIXTURES / d).is_dir(), d)
                    f = facts(d)
                    self.assertTrue(f["manifests"], "no manifest detected for " + d)
                    self.assertTrue(any(k in f["commands"] for k in ("install", "py_install", "build", "test", "scripts")),
                                    "no commands detected for " + d)


class NodeTest(unittest.TestCase):
    def test_npm(self):
        f = facts("node-npm")
        self.assertEqual(f["manifests"], ["package.json"])
        self.assertEqual(f["js_package_manager"], "npm")
        c = f["commands"]
        self.assertEqual(c["install"], "npm install")
        self.assertEqual(c["scripts"]["dev"], {"run": "npm run dev", "does": "vite"})
        self.assertEqual(c["scripts"]["start"]["run"], "npm start")
        self.assertEqual(c["scripts"]["test"]["run"], "npm test")
        self.assertEqual(f["frameworks"], ["React", "TypeScript", "Vite", "Vitest"])
        self.assertEqual(f["project_type_guess"], "webapp")

    def test_pnpm(self):
        f = facts("node-pnpm")
        self.assertEqual(f["js_package_manager"], "pnpm")
        self.assertEqual(f["commands"]["install"], "pnpm install")
        self.assertEqual(f["commands"]["scripts"]["dev"]["run"], "pnpm dev")
        self.assertEqual(f["commands"]["scripts"]["test"]["run"], "pnpm test")
        self.assertIn("Express", f["frameworks"])
        self.assertIn({"method": "GET", "path": "/health", "file": "server.js"}, f["http_routes"])
        self.assertEqual(f["project_type_guess"], "api")

    def test_yarn(self):
        f = facts("node-yarn")
        self.assertEqual(f["js_package_manager"], "yarn")
        self.assertEqual(f["commands"]["install"], "yarn")
        self.assertEqual(f["commands"]["scripts"]["build"]["run"], "yarn build")
        self.assertEqual(f["frameworks"], ["Next.js", "React"])
        self.assertIn("app/page.tsx", f["entrypoints"])

    def test_bun(self):
        f = facts("node-bun")
        self.assertEqual(f["js_package_manager"], "bun")
        self.assertEqual(f["commands"]["install"], "bun install")
        self.assertEqual(f["commands"]["scripts"]["dev"]["run"], "bun run dev")
        self.assertEqual(f["bins"], {"bun-cli": "./cli.ts"})
        self.assertIn("Commander (CLI)", f["frameworks"])
        self.assertTrue(f["package"]["publishable_npm"])
        self.assertEqual(f["project_type_guess"], "cli")


class PythonTest(unittest.TestCase):
    def test_pip_requirements(self):
        f = facts("python-pip-requirements")
        self.assertEqual(f["manifests"], ["requirements.txt"])
        self.assertEqual(f["commands"]["py_install"], "pip install -r requirements.txt")
        self.assertEqual(f["frameworks"], ["Flask", "pytest"])
        self.assertEqual(sorted(f["env_vars"]), ["FLASK_SECRET_KEY"])
        self.assertEqual(f["env_vars"]["FLASK_SECRET_KEY"]["source"], "app.py")

    def test_uv(self):
        f = facts("python-uv")
        self.assertEqual(f["manifests"], ["pyproject.toml"])
        self.assertEqual(f["py_package_manager"], "uv")
        self.assertEqual(f["commands"]["py_install"], "uv sync")
        self.assertEqual(f["commands"]["lint"], "ruff check .")
        self.assertEqual(f["bins"], {"uvtool": "uvtool.cli:main"})
        self.assertEqual(f["package"]["pypi_install"], "pip install uvtool")
        self.assertEqual(f["package"]["requires_python"], ">=3.9")
        self.assertEqual(f["frameworks"], ["Click (CLI)"])
        self.assertEqual(f["project_type_guess"], "cli")

    def test_poetry(self):
        f = facts("python-poetry")
        self.assertEqual(f["py_package_manager"], "poetry")
        self.assertEqual(f["commands"]["py_install"], "poetry install")
        self.assertEqual(f["commands"]["test"], "pytest")
        self.assertEqual(f["bins"], {"poetry-api": "poetry_api.main:run"})
        self.assertEqual(f["frameworks"], ["FastAPI"])
        self.assertEqual(f["project_type_guess"], "api")

    def test_pdm(self):
        f = facts("python-pdm")
        self.assertEqual(f["py_package_manager"], "pdm")
        self.assertEqual(f["commands"]["py_install"], "pdm install")
        self.assertEqual(f["project_type_guess"], "library")

    def test_hatch(self):
        f = facts("python-hatch")
        self.assertEqual(f["py_package_manager"], "hatch")
        self.assertEqual(f["commands"]["py_install"], "pip install -e .")
        self.assertIn("Pydantic", f["frameworks"])

    def test_setup_py(self):
        f = facts("python-setup-py")
        self.assertEqual(f["manifests"], ["setup.py"])
        self.assertEqual(f["commands"]["py_install"], "pip install -e .")
        self.assertEqual(f["package"]["name"], "legacy-pkg")

    def test_pipenv(self):
        f = facts("python-pipenv")
        self.assertEqual(f["manifests"], ["Pipfile"])
        self.assertEqual(f["commands"]["py_install"], "pipenv install")

    def test_conda(self):
        f = facts("python-conda")
        self.assertEqual(f["manifests"], ["environment.yml"])
        self.assertEqual(f["commands"]["py_install"], "conda env create -f environment.yml")


class CompiledEcosystemTest(unittest.TestCase):
    def test_rust(self):
        f = facts("rust")
        self.assertEqual(f["manifests"], ["Cargo.toml"])
        self.assertEqual({k: f["commands"][k] for k in ("build", "test", "run")},
                         {"build": "cargo build --release", "test": "cargo test", "run": "cargo run"})
        self.assertEqual(f["frameworks"], ["Tokio", "clap (CLI)"])
        self.assertEqual(f["package"]["cargo_install"], "cargo install rtool")
        self.assertEqual(sorted(f["env_vars"]), ["RTOOL_TOKEN"])
        self.assertEqual(f["project_type_guess"], "cli")

    def test_go_with_cmd_dir(self):
        f = facts("go")
        self.assertEqual(f["manifests"], ["go.mod"])
        self.assertEqual(f["commands"]["build"], "go build ./...")
        self.assertEqual(f["commands"]["test"], "go test ./...")
        self.assertEqual(f["package"]["go_module"], "example.com/gotool")
        self.assertEqual(f["package"]["go_version"], "1.22")
        # no main package at the module root, so install the command under cmd/
        self.assertEqual(f["package"]["go_install"], "go install example.com/gotool/cmd/gotool@latest")
        self.assertEqual(f["go_cmds"], ["gotool"])
        self.assertEqual(f["bins"], {"gotool": "./cmd/gotool"})
        self.assertEqual(f["frameworks"], ["Cobra (CLI)"])
        self.assertEqual(sorted(f["env_vars"]), ["GOTOOL_HOME"])

    def test_maven_spring_boot(self):
        f = facts("maven")
        self.assertEqual(f["manifests"], ["pom.xml"])
        self.assertEqual(f["commands"]["build"], "mvn package")
        self.assertEqual(f["commands"]["test"], "mvn test")
        self.assertEqual(f["frameworks"], ["Spring Boot"])
        # com/example is a Java package, not a sample dir: its env vars belong to the project
        self.assertEqual(f["example_dirs"], [])
        self.assertEqual(sorted(f["env_vars"]), ["DB_URL"])

    def test_gradle_wrapper(self):
        f = facts("gradle")
        self.assertEqual(f["manifests"], ["build.gradle"])
        self.assertEqual(f["commands"]["build"], "./gradlew build")
        self.assertEqual(f["commands"]["test"], "./gradlew test")
        self.assertEqual(f["frameworks"], ["Spring Boot"])

    def test_gradle_android_without_wrapper(self):
        f = facts("gradle-android")
        self.assertEqual(f["manifests"], ["build.gradle.kts"])
        self.assertEqual(f["commands"]["build"], "gradle build")
        self.assertEqual(f["frameworks"], ["Android"])

    def test_dotnet(self):
        f = facts("dotnet")
        self.assertEqual(f["manifests"], ["Api.csproj"])
        self.assertEqual({k: f["commands"][k] for k in ("build", "test", "run")},
                         {"build": "dotnet build", "test": "dotnet test", "run": "dotnet run"})
        self.assertIn("Program.cs", f["entrypoints"])

    def test_cmake(self):
        f = facts("cmake")
        self.assertEqual(f["manifests"], ["CMakeLists.txt"])
        self.assertEqual(f["commands"]["build"], "cmake -B build && cmake --build build")

    def test_swift(self):
        f = facts("swift")
        self.assertEqual(f["manifests"], ["Package.swift"])
        self.assertEqual({k: f["commands"][k] for k in ("build", "test", "run")},
                         {"build": "swift build", "test": "swift test", "run": "swift run"})
        self.assertEqual(f["frameworks"], ["Vapor"])
        self.assertEqual(f["project_type_guess"], "api")

    def test_zig(self):
        f = facts("zig")
        self.assertEqual(f["manifests"], ["build.zig"])
        self.assertEqual(f["commands"], {"build": "zig build", "test": "zig build test"})
        self.assertEqual(f["project_type_guess"], "library")

    def test_haskell_stack(self):
        f = facts("haskell-stack")
        self.assertEqual(f["manifests"], ["stack.yaml", "hs-app.cabal"])
        self.assertEqual(f["commands"], {"build": "stack build", "test": "stack test"})

    def test_haskell_cabal(self):
        f = facts("haskell-cabal")
        self.assertEqual(f["manifests"], ["mylib.cabal"])
        self.assertEqual(f["commands"], {"build": "cabal build", "test": "cabal test"})
        self.assertEqual(f["project_type_guess"], "library")


class ScriptingEcosystemTest(unittest.TestCase):
    def test_ruby_rails(self):
        f = facts("ruby-rails")
        self.assertEqual(f["manifests"], ["Gemfile"])
        self.assertEqual(f["commands"]["install"], "bundle install")
        self.assertEqual(f["frameworks"], ["Ruby on Rails"])
        self.assertEqual(sorted(f["env_vars"]), ["STRIPE_API_KEY"])

    def test_php_laravel(self):
        f = facts("php-laravel")
        self.assertEqual(f["manifests"], ["composer.json"])
        self.assertEqual(f["commands"]["install"], "composer install")
        self.assertEqual(f["frameworks"], ["Laravel"])

    def test_flutter(self):
        f = facts("flutter")
        self.assertEqual(f["manifests"], ["pubspec.yaml"])
        self.assertEqual(f["commands"], {"install": "flutter pub get", "run": "flutter run", "test": "flutter test"})
        self.assertEqual(f["frameworks"], ["Flutter"])
        self.assertIn("lib/main.dart", f["entrypoints"])
        self.assertEqual(f["project_type_guess"], "mobile")

    def test_elixir_phoenix(self):
        f = facts("elixir-phoenix")
        self.assertEqual(f["manifests"], ["mix.exs"])
        self.assertEqual(f["commands"], {"install": "mix deps.get", "test": "mix test", "run": "mix phx.server"})
        self.assertEqual(f["frameworks"], ["Phoenix"])

    def test_deno(self):
        f = facts("deno")
        self.assertEqual(f["manifests"], ["deno.json"])
        self.assertEqual(f["frameworks"], ["Deno"])
        self.assertEqual(f["commands"]["test"], "deno test")
        self.assertEqual(f["commands"]["scripts"]["dev"], {"run": "deno task dev", "does": "deno run --watch main.ts"})
        self.assertEqual(sorted(f["env_vars"]), ["DENO_KV_TOKEN"])


class CrossCuttingFactsTest(unittest.TestCase):
    def test_make_and_just(self):
        c = facts("make-just")["commands"]
        self.assertEqual(c["make_targets"], ["build", "install", "test"])
        # `set shell := ...` and `version := ...` are assignments, not recipes
        self.assertEqual(c["just_recipes"], ["build", "default", "serve", "test"])

    def test_env_example_and_code_usage(self):
        f = facts("env-vars")
        env = f["env_vars"]
        self.assertEqual(sorted(env), ["API_KEY", "DATABASE_URL", "SESSION_SECRET"])
        self.assertEqual(env["DATABASE_URL"], {"source": ".env.example", "example": "postgres://localhost:5432/app"})
        self.assertEqual(env["API_KEY"]["example"], "changeme")
        self.assertEqual(env["SESSION_SECRET"], {"source": "src/server.js"})
        self.assertNotIn("NODE_ENV", env)        # ignored builtin
        self.assertNotIn("TEST_ONLY_VAR", env)   # test files are skipped
        self.assertNotIn("COMMENTED_OUT", env)

    def test_docker_compose(self):
        d = facts("docker-compose")["docker"]
        self.assertEqual(d["compose_file"], "docker-compose.yml")
        self.assertEqual(d["compose_services"], ["web", "db", "cache"])
        self.assertEqual(d["compose_up"], "docker compose up")
        self.assertEqual(d["exposed_ports"], ["3000"])
        self.assertEqual(d["base_images"], ["node:20-alpine"])

    def test_demo_dir_does_not_leak(self):
        f = facts("demo-isolation")
        self.assertEqual(sorted(f["env_vars"]), ["REAL_API_KEY"])
        for leaked in ("DEMO_ONLY_KEY", "DEMO_SECRET", "EXAMPLE_ONLY_VAR"):
            self.assertNotIn(leaked, f["env_vars"])
        self.assertEqual(f["example_dirs"], ["demo", "examples"])
        self.assertEqual(f["languages"][0]["name"], "JavaScript")
        self.assertEqual(f["languages"][0]["files"], 1)  # demo/app.js not counted


class CliTest(unittest.TestCase):
    def test_compact_json_output(self):
        out = subprocess.run([sys.executable, str(SCRIPTS / "analyze_repo.py"), str(FIXTURES / "rust"), "--compact"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        data = json.loads(out.stdout.decode("utf-8"))
        self.assertEqual(data["manifests"], ["Cargo.toml"])


if __name__ == "__main__":
    unittest.main()
