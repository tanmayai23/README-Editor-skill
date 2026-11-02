#!/usr/bin/env python3
"""Learn what each user wants from what they keep, change and delete.

Stdlib only. Everything stays on this machine: no network, no telemetry.

readme-forge makes choices for every README: banner style, palette, sections, length,
heading style. This script treats each choice as an arm of a contextual bandit (the
reinforcement-learning setting for one-step decisions). The context is the project
(mode, kind, language); the reward comes from the user. Edits are the signal: a section
the user deletes, a banner they regenerate or a README they cut by half is a 0 for that
choice; what survives is a 1. Thompson sampling then picks options that fit this user and
this kind of project, and still tries an alternative now and then while it is unsure.

Usage:
    python learn.py suggest --context mode=project,kind=cli --decision banner.style:beam,aurora,prism [--sections "Features,FAQ"] [--json]
    python learn.py snapshot README.md --context mode=project,kind=cli --choice banner.style=beam@file:.github/assets/header-dark.svg --choice length=standard
    python learn.py observe README.md [--accepted]      # learn from the user's edits since the snapshot
    python learn.py reward banner.style=beam --value 0 [--context ...]   # explicit feedback
    python learn.py prefer "never use emoji in headings" | prefer --list | prefer --remove 2
    python learn.py show | reset | off | on

`--repo PATH` on suggest/snapshot adds lang= and kind= from analyze_repo.py.
Data lives in ~/.readme-forge (override with READMEFORGE_HOME). READMEFORGE_LEARN=0 turns
learning off for one run; `learn.py off` turns it off until `learn.py on`.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import random
import re
import sys
import time
from datetime import date
from pathlib import Path

VERSION = 1
DECAY = 0.95            # older feedback counts less, so tastes can change
GLOBAL_WEIGHT = 0.5     # evidence from other contexts counts half
CONFIDENT = 3.0         # observations before a ranking is called confident
DROP_BELOW = 0.35       # keep-probability under which a section is suggested for removal
STALE_DAYS = 7          # an untouched README this old counts as accepted
HISTORY_MAX = 200
LENGTHS = ("concise", "standard", "detailed")
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
HEADING = re.compile(r"^(#{2,6})\s+(.+?)\s*#*\s*$", re.M)


def home() -> Path:
    return Path(os.environ.get("READMEFORGE_HOME") or Path.home() / ".readme-forge")


def store_path() -> Path:
    return home() / "learn.json"


def load() -> dict:
    try:
        data = json.loads(store_path().read_text(encoding="utf-8"))
        if data.get("version") == VERSION:
            return data
    except (OSError, ValueError):
        pass
    return {"version": VERSION, "enabled": True, "decisions": {}, "preferences": [], "history": []}


def save(data: dict) -> None:
    p = store_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, p)


def enabled(data: dict) -> bool:
    return os.environ.get("READMEFORGE_LEARN", "1") != "0" and data.get("enabled", True)


# ---------- context ----------

def parse_context(text: str | None) -> dict:
    ctx = {}
    for part in (text or "").split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            if k.strip() and v.strip():
                ctx[k.strip().lower()] = v.strip().lower()
    return ctx


def repo_context(repo: str | None) -> dict:
    if not repo:
        return {}
    spec = importlib.util.spec_from_file_location("rf_analyze_repo", str(Path(__file__).with_name("analyze_repo.py")))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    facts = mod.analyze(Path(repo))
    ctx = {"kind": mod.guess_type(facts)}
    if facts.get("primary_language"):
        ctx["lang"] = facts["primary_language"].lower()
    return ctx


def buckets(ctx: dict):
    return ["*"] + [f"{k}={v}" for k, v in sorted(ctx.items())]


# ---------- the bandit ----------

def update(data: dict, decision: str, option: str, reward: float, ctx: dict, source: str) -> None:
    reward = min(1.0, max(0.0, float(reward)))
    arms = data["decisions"].setdefault(decision, {})
    for opt in arms.values():
        for counts in opt.values():
            counts[0] *= DECAY
            counts[1] *= DECAY
    arm = arms.setdefault(option, {})
    for b in buckets(ctx):
        counts = arm.setdefault(b, [0.0, 0.0])
        counts[0] += reward
        counts[1] += 1.0 - reward
    data["history"].append({"date": date.today().isoformat(), "decision": decision, "option": option,
                            "reward": round(reward, 2), "context": ctx, "source": source})
    del data["history"][:-HISTORY_MAX]


def posterior(data: dict, decision: str, option: str, ctx: dict):
    """Beta(alpha, beta) for one option: global evidence at half weight plus the
    average of the evidence collected in each matching context feature."""
    arm = data["decisions"].get(decision, {}).get(option, {})
    g = arm.get("*", [0.0, 0.0])
    feats = [arm.get(b, [0.0, 0.0]) for b in buckets(ctx)[1:]]
    if feats:
        s = GLOBAL_WEIGHT * g[0] + sum(f[0] for f in feats) / len(feats)
        f = GLOBAL_WEIGHT * g[1] + sum(f[1] for f in feats) / len(feats)
    else:
        s, f = g
    return 1.0 + s, 1.0 + f


def rank(data: dict, decision: str, options, ctx: dict, rng: random.Random) -> dict:
    """Rank options by posterior mean. `pick` is a Thompson sample, so an option that
    hasn't been tried enough still gets chosen sometimes. With no evidence at all the
    pick is the first option given, which keeps the skill's own default."""
    seen = list(data["decisions"].get(decision, {}))
    order = list(dict.fromkeys(list(options) + seen))
    rows = []
    for i, opt in enumerate(order):
        a, b = posterior(data, decision, opt, ctx)
        rows.append({"option": opt, "mean": round(a / (a + b), 3), "evidence": round(a + b - 2, 2),
                     "_sample": rng.betavariate(a, b), "_i": i})
    total = sum(r["evidence"] for r in rows)
    pick = max(rows, key=lambda r: r["_sample"])["option"] if total > 0 else (order[0] if order else None)
    rows.sort(key=lambda r: (-r["mean"], r["_i"]))
    for r in rows:
        del r["_sample"], r["_i"]
    return {"decision": decision, "pick": pick, "confident": total >= CONFIDENT, "ranking": rows}


# ---------- README reading ----------

def slug(text: str) -> str:
    text = EMOJI.sub("", re.sub(r"<[^>]+>|[`*_]|\[([^\]]*)\]\([^)]*\)", r"\1", text))
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def sections(text: str) -> dict:
    """H2+ headings outside code fences, as {slug: heading text}."""
    plain = re.sub(r"^(```|~~~).*?^\1", "", text, flags=re.M | re.S)
    out = {}
    for m in HEADING.finditer(plain):
        s = slug(m.group(2))
        if s:
            out.setdefault(s, m.group(2))
    return out


def words(text: str) -> int:
    return len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", text)))


def emoji_headings(text: str) -> bool:
    return any(EMOJI.search(h) for h in sections(text).values())


def file_hash(path: Path):
    try:
        return hashlib.sha1(path.read_bytes()).hexdigest()
    except OSError:
        return None


def snapshot_path(readme: Path) -> Path:
    key = hashlib.sha1(str(readme.resolve()).lower().encode("utf-8")).hexdigest()[:16]
    return home() / "snapshots" / f"{key}.json"


def parse_choice(text: str) -> dict:
    """decision=option[@marker]; marker is text that must survive in the README, or
    file:<path> for a generated asset that must stay referenced and unchanged."""
    if "=" not in text:
        raise SystemExit(f"error: --choice needs decision=option, got {text!r}")
    decision, rest = text.split("=", 1)
    option, _, marker = rest.partition("@")
    return {"decision": decision.strip(), "option": option.strip(), "marker": marker.strip() or None}


# ---------- learning from edits ----------

def judge(snap: dict, now: str, readme: Path) -> list:
    """Turn the difference between the generated README and the current one into rewards."""
    rewards = []
    base = readme.parent
    for c in snap["choices"]:
        d, opt, marker = c["decision"], c["option"], c.get("marker")
        if d == "length":
            ratio = words(now) / max(1, snap["words"])
            implied = "concise" if ratio < 0.75 else "detailed" if ratio > 1.33 else opt
            rewards.append((d, opt, 1.0 if implied == opt else 0.0, f"length ratio {ratio:.2f}"))
            if implied != opt:
                rewards.append((d, implied, 1.0, f"length ratio {ratio:.2f}"))
        elif marker and marker.startswith("file:"):
            rel = marker[5:]
            still = rel in now and file_hash(base / rel) == c.get("hash")
            rewards.append((d, opt, 1.0 if still else 0.0, f"{rel} {'kept' if still else 'changed or removed'}"))
        elif marker:
            rewards.append((d, opt, 1.0 if marker in now else 0.0, "kept" if marker in now else "removed"))
    before, after = set(snap["sections"]), set(sections(now))
    for s in sorted(before):
        rewards.append((f"section:{s}", "keep", 1.0 if s in after else 0.0, "kept" if s in after else "deleted"))
    for s in sorted(after - before):
        rewards.append((f"section:{s}", "keep", 1.0, "added by the user"))
    had, has = snap["emoji_headings"], emoji_headings(now)
    if had != has:
        rewards.append(("headings.emoji", "yes" if has else "no", 1.0, "user changed heading emoji"))
        rewards.append(("headings.emoji", "yes" if had else "no", 0.0, "user changed heading emoji"))
    return rewards


# ---------- commands ----------

def cmd_suggest(args, data):
    ctx = {**repo_context(args.repo), **parse_context(args.context)}
    rng = random.Random(args.seed)
    out = {"context": ctx, "learning": enabled(data), "decisions": [], "sections": [],
           "preferences": [p["text"] for p in data["preferences"]]}
    for spec in args.decision or []:
        name, _, opts = spec.partition(":")
        out["decisions"].append(rank(data, name.strip(), [o.strip() for o in opts.split(",") if o.strip()], ctx, rng))
    names = [s.strip() for s in (args.sections or "").split(",") if s.strip()]
    seen = [d[8:] for d in data["decisions"] if d.startswith("section:")]
    for s in list(dict.fromkeys([slug(n) for n in names] + ([] if names else seen))):
        a, b = posterior(data, f"section:{s}", "keep", ctx)
        mean, n = a / (a + b), a + b - 2
        out["sections"].append({"section": s, "keep": round(mean, 3), "evidence": round(n, 2),
                                "advice": "omit" if n >= 2 and mean < DROP_BELOW else "include"})
    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0
    if not out["learning"]:
        print("learning is off: suggestions use defaults only")
    for p in out["preferences"]:
        print(f"preference: {p}")
    for d in out["decisions"]:
        top = ", ".join(f"{r['option']} {r['mean']:.2f}" for r in d["ranking"][:4])
        print(f"{d['decision']}: use {d['pick']}{'' if d['confident'] else ' (still learning)'}  [{top}]")
    for s in out["sections"]:
        print(f"section {s['section']}: {s['advice']} (keep {s['keep']:.2f}, {s['evidence']:.1f} obs)")
    return 0


def cmd_snapshot(args, data):
    if not enabled(data):
        print("learning is off: no snapshot taken")
        return 0
    readme = Path(args.readme)
    text = readme.read_text(encoding="utf-8", errors="replace")
    choices = [parse_choice(c) for c in args.choice or []]
    for c in choices:
        if c["marker"] and c["marker"].startswith("file:"):
            c["hash"] = file_hash(readme.parent / c["marker"][5:])
    snap = {"readme": str(readme.resolve()), "created": time.time(),
            "context": {**repo_context(args.repo), **parse_context(args.context)},
            "choices": choices, "sections": sorted(sections(text)), "words": words(text),
            "emoji_headings": emoji_headings(text), "text_hash": hashlib.sha1(text.encode("utf-8")).hexdigest()}
    p = snapshot_path(readme)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(snap, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"snapshot of {readme}: {len(choices)} choices, {len(snap['sections'])} sections")
    return 0


def cmd_observe(args, data):
    readme = Path(args.readme)
    p = snapshot_path(readme)
    if not enabled(data) or not p.exists():
        print("nothing to learn: no snapshot for this README" if enabled(data) else "learning is off")
        return 0
    snap = json.loads(p.read_text(encoding="utf-8"))
    now = readme.read_text(encoding="utf-8", errors="replace") if readme.exists() else ""
    unchanged = hashlib.sha1(now.encode("utf-8")).hexdigest() == snap["text_hash"]
    stale = time.time() - snap["created"] > STALE_DAYS * 86400
    if unchanged and not (args.accepted or stale):
        print("no edits since the snapshot yet: run again after the user has reviewed it, or pass --accepted")
        return 0
    rewards = judge(snap, now, readme)
    for d, opt, r, why in rewards:
        update(data, d, opt, r, snap["context"], "edit")
    save(data)
    p.unlink()
    if args.json:
        print(json.dumps([{"decision": d, "option": o, "reward": r, "why": w} for d, o, r, w in rewards], indent=2))
    else:
        print(f"learned {len(rewards)} signals from {readme}:")
        for d, opt, r, why in rewards:
            print(f"  {'+' if r >= 0.5 else '-'} {d}={opt}  ({why})")
    return 0


def cmd_reward(args, data):
    if not enabled(data):
        print("learning is off")
        return 0
    c = parse_choice(args.choice)
    update(data, c["decision"], c["option"], args.value, {**repo_context(args.repo), **parse_context(args.context)}, "explicit")
    save(data)
    print(f"recorded {c['decision']}={c['option']} reward {args.value}")
    return 0


def cmd_prefer(args, data):
    prefs = data["preferences"]
    if args.remove:
        if not 1 <= args.remove <= len(prefs):
            print(f"error: no preference #{args.remove}", file=sys.stderr)
            return 2
        gone = prefs.pop(args.remove - 1)
        save(data)
        print(f"removed: {gone['text']}")
        return 0
    if args.text:
        if not enabled(data):
            print("learning is off")
            return 0
        if args.text not in [p["text"] for p in prefs]:
            prefs.append({"text": args.text, "added": date.today().isoformat()})
            save(data)
        print(f"saved preference: {args.text}")
        return 0
    for i, p in enumerate(prefs, 1):
        print(f"{i}. {p['text']}  ({p['added']})")
    if not prefs:
        print("no saved preferences")
    return 0


def cmd_show(args, data):
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0
    print(f"learning: {'on' if enabled(data) else 'off'}  ·  store: {store_path()}")
    for i, p in enumerate(data["preferences"], 1):
        print(f"preference {i}: {p['text']}")
    for name in sorted(data["decisions"]):
        rows = []
        for opt in data["decisions"][name]:
            a, b = posterior(data, name, opt, {})
            rows.append((a / (a + b), a + b - 2, opt))
        rows.sort(reverse=True)
        print(f"{name}: " + ", ".join(f"{o} {m:.2f} ({n:.1f})" for m, n, o in rows))
    if not data["decisions"] and not data["preferences"]:
        print("nothing learned yet")
    return 0


def cmd_reset(args, data):
    for p in (home() / "snapshots").glob("*.json"):
        p.unlink()
    save({"version": VERSION, "enabled": data.get("enabled", True), "decisions": {}, "preferences": [], "history": []})
    print("forgot everything learned (preferences, rewards and snapshots)")
    return 0


def cmd_toggle(on):
    def run(args, data):
        data["enabled"] = on
        save(data)
        print(f"learning is {'on' if on else 'off'}")
        return 0
    return run


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="learn.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("suggest", help="rank options for this context")
    s.add_argument("--context")
    s.add_argument("--repo")
    s.add_argument("--decision", action="append", help="name:opt1,opt2 (first option is the default)")
    s.add_argument("--sections", help="comma-separated section names to rate")
    s.add_argument("--seed", type=int)
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_suggest)

    s = sub.add_parser("snapshot", help="remember what was generated")
    s.add_argument("readme")
    s.add_argument("--context")
    s.add_argument("--repo")
    s.add_argument("--choice", action="append", help="decision=option[@marker]")
    s.set_defaults(fn=cmd_snapshot)

    s = sub.add_parser("observe", help="learn from edits made since the snapshot")
    s.add_argument("readme")
    s.add_argument("--accepted", action="store_true", help="the user approved it as is")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_observe)

    s = sub.add_parser("reward", help="record explicit feedback")
    s.add_argument("choice", help="decision=option")
    s.add_argument("--value", type=float, required=True, help="0 (rejected) to 1 (liked)")
    s.add_argument("--context")
    s.add_argument("--repo")
    s.set_defaults(fn=cmd_reward)

    s = sub.add_parser("prefer", help="save, list or remove a stated preference")
    s.add_argument("text", nargs="?")
    s.add_argument("--list", action="store_true")
    s.add_argument("--remove", type=int)
    s.set_defaults(fn=cmd_prefer)

    s = sub.add_parser("show", help="print what has been learned")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_show)

    sub.add_parser("reset", help="forget everything").set_defaults(fn=cmd_reset)
    sub.add_parser("off", help="stop learning").set_defaults(fn=cmd_toggle(False))
    sub.add_parser("on", help="resume learning").set_defaults(fn=cmd_toggle(True))

    args = ap.parse_args(argv)
    return args.fn(args, load())


if __name__ == "__main__":
    sys.exit(main())
