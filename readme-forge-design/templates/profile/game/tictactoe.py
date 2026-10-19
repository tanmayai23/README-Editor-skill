#!/usr/bin/env python3
"""Community tic-tac-toe for a GitHub profile README (Game Mode).

Visitors click an empty square, which opens an issue titled `ttt|move|N`. The
workflow `workflows/tictactoe.yml` runs this script, which plays the move for
the team whose turn it is, redraws the board between the TICTACTOE markers in
README.md, and prints the reply the workflow posts on the issue.

Copy this file to `.github/scripts/tictactoe.py` in the USER/USER repo.
Standard library only. Exit 0 = move played, 1 = move rejected (reason on stdout).

  python tictactoe.py --repo USER/USER --title "ttt|move|5" --user octocat
  python tictactoe.py --repo USER/USER --render     # just (re)draw the board
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

START, END = "<!-- TICTACTOE:START -->", "<!-- TICTACTOE:END -->"
LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
MARK = {"X": "❌", "O": "⭕"}


def new_state(old: dict | None = None) -> dict:
    old = old or {}
    return {"board": [""] * 9, "turn": "X", "last_player": None,
            "moves": old.get("moves", []), "score": old.get("score", {"X": 0, "O": 0, "draw": 0}),
            "players": old.get("players", 0), "seen": old.get("seen", [])}


def winner(board: list) -> str | None:
    for a, b, c in LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    return "draw" if all(board) else None


def play(state: dict, title: str, user: str) -> tuple[bool, str]:
    m = re.fullmatch(r"\s*ttt\|move\|([1-9])\s*", title or "")
    if not m:
        return False, "That issue title isn't a move. Click an empty square in the README to play."
    sq = int(m.group(1)) - 1
    if state["board"][sq]:
        return False, f"Square {sq + 1} is already taken. Pick another empty square in the README."
    if user and user == state.get("last_player"):
        return False, "You made the last move. Let someone else play the other team, then go again."
    team = state["turn"]
    state["board"][sq] = team
    state["last_player"] = user
    state["moves"] = ([{"team": team, "square": sq + 1, "user": user}] + state["moves"])[:5]
    if user and user not in state["seen"]:
        state["seen"].append(user)
        state["players"] += 1
    result = winner(state["board"])
    if result:
        state["score"][result] += 1
        msg = "It's a draw." if result == "draw" else f"{MARK[team]} wins with your move! 🎉"
        state.update({k: v for k, v in new_state(state).items() if k in ("board", "turn", "last_player")})
        return True, f"You played {MARK[team]} on square {sq + 1}. {msg} A new game has started."
    state["turn"] = "O" if team == "X" else "X"
    return True, f"You played {MARK[team]} on square {sq + 1}. It's {MARK[state['turn']]}'s turn now."


def render(state: dict, repo: str) -> str:
    def cell(i: int) -> str:
        if state["board"][i]:
            return MARK[state["board"][i]]
        url = (f"https://github.com/{repo}/issues/new?title={quote(f'ttt|move|{i + 1}')}"
               f"&body={quote('Just click Submit new issue. A bot plays your move within a minute.')}")
        return f"[{i + 1}]({url})"
    rows = ["| | | |", "|:-:|:-:|:-:|"] + ["| " + " | ".join(cell(r * 3 + c) for c in range(3)) + " |" for r in range(3)]
    s = state["score"]
    out = [START, "", f"**It's {MARK[state['turn']]}'s turn.** Click a numbered square to play it.", ""] + rows + [""]
    out.append(f"❌ wins: **{s['X']}** · ⭕ wins: **{s['O']}** · Draws: **{s['draw']}** · Players: **{state['players']}**")
    if state["moves"]:
        out += ["", "| Team | Square | Played by |", "| --- | --- | --- |"]
        out += [f"| {MARK[m['team']]} | {m['square']} | [@{m['user']}](https://github.com/{m['user']}) |" for m in state["moves"]]
    return "\n".join(out + ["", END])


def write_readme(readme: Path, block: str) -> None:
    text = readme.read_text(encoding="utf-8")
    if START not in text or END not in text:
        sys.exit(f"{readme} has no {START} … {END} markers")
    pre, rest = text.split(START, 1)
    readme.write_text(pre + block + rest.split(END, 1)[1], encoding="utf-8")


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--repo", required=True, help="OWNER/REPO the README lives in")
    p.add_argument("--title", default="", help="issue title, e.g. ttt|move|5")
    p.add_argument("--user", default="", help="login of the issue author")
    p.add_argument("--state", default=".github/game/tictactoe.json")
    p.add_argument("--readme", default="README.md")
    p.add_argument("--render", action="store_true", help="only redraw the board")
    a = p.parse_args(argv)
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", a.repo) or (a.user and not re.fullmatch(r"[\w-]+(\[bot\])?", a.user)):
        print("Invalid --repo or --user.")
        return 1
    sp = Path(a.state)
    state = json.loads(sp.read_text(encoding="utf-8")) if sp.is_file() else new_state()
    ok, msg = (True, "Board redrawn.") if a.render else play(state, a.title, a.user)
    if ok:
        sp.parent.mkdir(parents=True, exist_ok=True)
        sp.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        write_readme(Path(a.readme), render(state, a.repo))
    print(msg)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
