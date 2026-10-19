# node-app

A tiny Express API used as a fixture: every claim in this file is true.

<!-- TODO: add a demo GIF -->

## Quickstart

```bash
git status
cd ..
cd node-app
pnpm install
cp .env.example .env   # then fill in DATABASE_URL
pnpm dev
```

```console
$ pnpm run dev
listening on http://localhost:3000
$ curl http://localhost:3000/health
{"ok":true}
```

Run the tests with `pnpm test`. Check your Node version with `node --version`.

## Docker

```sh
docker compose up -d api db
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | — | PostgreSQL connection string |
| `STRIPE_KEY` | — | Stripe secret key |
| `PORT` | `3000` | HTTP port |

```text
src/
└── index.js    # Express app
```

The app lives in [src/index.js](src/index.js) and reads `.env.example` values.
