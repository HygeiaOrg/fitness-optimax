#!/usr/bin/env python3
"""Keep the Log Workout exercise catalogue in step with the NTB programme.

North Tyneside Barbells publish a monthly programme spreadsheet (one tab per
week, "Exercise | sets | reps | % ..." blocks per session). This script reads
an .xlsx export of it and compares the exercises against
frontend/src/data/exercises.json.

    python scripts/sync_exercises.py diff PROGRAMME.xlsx
        Print JSON: exercises in the programme that the catalogue doesn't
        cover yet ("new"), and the ones it already does ("known").

    python scripts/sync_exercises.py apply PROGRAMME.xlsx MAPPING.json
        Add the new exercises. MAPPING.json maps each programme name to
        {"name": <catalogue name>, "category": <existing category label>}.
        To create a category, add "new_category": true; it goes just before
        "General". Nothing is written unless the result passes validate.

    python scripts/sync_exercises.py validate [PROGRAMME.xlsx]
        Check the catalogue's invariants and, if a programme is given, that
        every exercise in it is covered. Exits 1 on any problem.

Only the standard library and openpyxl are needed.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CATALOGUE = Path(__file__).resolve().parent.parent / "frontend" / "src" / "data" / "exercises.json"

# BigQuery INITCAP's default delimiters: whitespace plus these characters.
_INITCAP_DELIMS = set(" \t\n\r[](){}/|\\<>!?@\"^#$&~_,.:;*%+-")


def initcap(s: str) -> str:
    """Python equivalent of BigQuery INITCAP() with default delimiters."""
    out, start = [], True
    for ch in s:
        out.append(ch.upper() if start else ch.lower())
        start = ch in _INITCAP_DELIMS
    return "".join(out)


def clean(name: str) -> str:
    """Trim and collapse internal whitespace ("Power  Snatch " -> "Power Snatch")."""
    return re.sub(r"\s+", " ", name).strip()


def extract(path: str | Path) -> list[str]:
    """Return the distinct exercise names in a programme workbook, sorted.

    An exercise is any text cell under an "Exercise" header whose neighbour
    in the "sets" column is a number; note rows and blank rows are skipped.
    """
    import openpyxl

    wb = openpyxl.load_workbook(path, data_only=True, read_only=False)
    names: set[str] = set()
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if not (isinstance(cell.value, str) and cell.value.strip().lower() == "exercise"):
                    continue
                col = cell.column
                for r in range(cell.row + 1, ws.max_row + 1):
                    v = ws.cell(r, col).value
                    sets = ws.cell(r, col + 1).value
                    if isinstance(v, str) and v.strip().lower() == "exercise":
                        break
                    if isinstance(v, str) and v.strip() and isinstance(sets, (int, float)):
                        names.add(clean(v))
    return sorted(names)


def load() -> dict:
    return json.loads(CATALOGUE.read_text(encoding="utf-8"))


def save(cat: dict) -> None:
    CATALOGUE.write_text(json.dumps(cat, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def catalogue_names(cat: dict) -> list[str]:
    return [e for c in cat["categories"] for e in c["exercises"]]


def resolve(name: str, cat: dict) -> str | None:
    """Catalogue name a programme name maps to, or None if not covered."""
    lower = {n.lower(): n for n in catalogue_names(cat)}
    aliases = {clean(k).lower(): v for k, v in cat.get("aliases", {}).items()}
    key = clean(name).lower()
    if key in aliases:
        return aliases[key]
    return lower.get(key)


def diff(path: str) -> dict:
    cat = load()
    new, known = [], {}
    for n in extract(path):
        hit = resolve(n, cat)
        if hit:
            known[n] = hit
        else:
            new.append(n)
    return {"new": new, "known": known}


def apply(path: str, mapping_path: str) -> list[str]:
    cat = load()
    mapping = json.loads(Path(mapping_path).read_text(encoding="utf-8"))
    pending = diff(path)["new"]
    missing = [n for n in pending if n not in mapping]
    if missing:
        raise SystemExit(f"MAPPING.json has no entry for: {missing}")
    added = []
    for prog_name in pending:
        target, label = mapping[prog_name]["name"], mapping[prog_name]["category"]
        if clean(prog_name) != target:
            cat.setdefault("aliases", {})[clean(prog_name)] = target
        if target.lower() in (n.lower() for n in catalogue_names(cat)):
            continue  # alias onto an existing exercise
        group = next((c for c in cat["categories"] if c["label"] == label), None)
        if group is None:
            if not mapping[prog_name].get("new_category"):
                raise SystemExit(
                    f"Unknown category {label!r} for {prog_name!r}; use an existing one "
                    f"or set \"new_category\": true")
            group = {"label": label, "exercises": []}
            idx = next((i for i, c in enumerate(cat["categories"]) if c["label"] == "General"), len(cat["categories"]))
            cat["categories"].insert(idx, group)
        group["exercises"].append(target)
        added.append(target)
    errs = problems(cat)
    if errs:
        raise SystemExit("Not saved; the catalogue would be invalid:\n  " + "\n  ".join(errs))
    save(cat)
    return added


def problems(cat: dict, programme: str | None = None) -> list[str]:
    errs = []
    names = catalogue_names(cat)
    seen = set()
    for n in names:
        if n.lower() in seen:
            errs.append(f"duplicate exercise: {n!r}")
        seen.add(n.lower())
        if "/" in n:
            errs.append(f"{n!r} contains '/', which breaks /api/charts/{{exercise_group}}")
        if initcap(n) != n:
            errs.append(f"{n!r} changes under INITCAP() to {initcap(n)!r}; logged rows would not match")
        if n != clean(n):
            errs.append(f"{n!r} has stray whitespace")
    for k, v in cat.get("aliases", {}).items():
        if v.lower() not in seen:
            errs.append(f"alias {k!r} points at {v!r}, which is not in the catalogue")
    for c in cat["categories"]:
        if not c.get("label") or not c.get("exercises"):
            errs.append(f"category {c.get('label')!r} is empty or unlabeled")
    if programme:
        for n in diff(programme)["new"]:
            errs.append(f"programme exercise not in catalogue: {n!r}")
    return errs


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in {"diff", "apply", "validate", "extract"}:
        print(__doc__)
        return 2
    cmd, args = argv[0], argv[1:]
    if cmd == "extract":
        print(json.dumps(extract(args[0]), indent=2))
    elif cmd == "diff":
        print(json.dumps(diff(args[0]), indent=2))
    elif cmd == "apply":
        print(json.dumps({"added": apply(args[0], args[1])}, indent=2))
    else:
        errs = problems(load(), args[0] if args else None)
        for e in errs:
            print("FAIL", e)
        print("OK" if not errs else f"{len(errs)} problem(s)")
        return 1 if errs else 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
