# py-cli-tool

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -r requirements-dev.txt
```

## Usage

```bash
tool --verbose --out result.json
python -m pkg --help
```

## Development

```bash
make test
make lint
python --version
```

The CLI is defined in `pkg/cli.py`.
