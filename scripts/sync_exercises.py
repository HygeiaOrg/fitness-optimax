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
        Only Olympic lifts and their derivatives get their own entry (category
        "Olympic Derivatives"); anything else is mapped onto the muscle group
        it trains (e.g. {"name": "Leg, Quads", "category": "Legs & Hips"}),
        which just records an alias. To create a category, add
        "new_category": true and "kind". Add "one_rm_base": <lift> when the
        programme prescribes an Olympic derivative as a % of another lift's
        1RM (e.g. "of Snatch"). Nothing is written unless the result passes
        validate; sql/01_stg_workouts.sql is regenerated alongside.

    python scripts/sync_exercises.py sql
        Regenerate the exercise map in sql/01_stg_workouts.sql from the
        catalogue (BigQuery uses it to roll history up into catalogue entries).

    python scripts/sync_exercises.py validate [PROGRAMME.xlsx]
        Check the catalogue's invariants, that the SQL exercise map is in
        step with it and, if a programme is given, that every exercise in it
        is covered. Exits 1 on any problem.

Only the standard library and openpyxl are needed.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOGUE = ROOT / "frontend" / "src" / "data" / "exercises.json"
STG_SQL = ROOT / "sql" / "01_stg_workouts.sql"
SQL_BEGIN = "-- BEGIN GENERATED exercise_map (python scripts/sync_exercises.py sql)"
SQL_END = "-- END GENERATED exercise_map"
KINDS = {"olympic", "muscle_group"}

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
            group = {"label": label, "kind": mapping[prog_name].get("kind", "olympic"), "exercises": []}
            cat["categories"].append(group)
        group["exercises"].append(target)
        base = mapping[prog_name].get("one_rm_base")
        if base and base != target:
            cat.setdefault("one_rm_base", {})[target] = base
        added.append(target)
    errs = problems(cat)
    if errs:
        raise SystemExit("Not saved; the catalogue would be invalid:\n  " + "\n  ".join(errs))
    save(cat)
    write_sql(cat)
    return added


def exercise_map(cat: dict) -> list[tuple[str, str]]:
    """(name as BigQuery sees it after INITCAP, catalogue entry) pairs: every
    catalogue entry maps to itself, every alias to its target."""
    pairs = {initcap(n): n for n in catalogue_names(cat)}
    for k, v in cat.get("aliases", {}).items():
        pairs.setdefault(initcap(clean(k)), v)
    return sorted(pairs.items())


def _sql_str(s: str) -> str:
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


def sql_block(cat: dict) -> str:
    rows = ",\n".join(
        f"    STRUCT({_sql_str(raw)} AS raw_name, {_sql_str(target)} AS exercise_group)"
        for raw, target in exercise_map(cat)
    )
    return f"{SQL_BEGIN}\n  SELECT raw_name, exercise_group FROM UNNEST([\n{rows}\n  ])\n  {SQL_END}"


def _split_sql(text: str) -> tuple[str, str, str]:
    start, end = text.find(SQL_BEGIN), text.find(SQL_END)
    if start < 0 or end < 0:
        raise SystemExit(f"{STG_SQL} has no generated exercise_map block")
    return text[:start], text[start:end + len(SQL_END)], text[end + len(SQL_END):]


def write_sql(cat: dict) -> None:
    before, _, after = _split_sql(STG_SQL.read_text(encoding="utf-8"))
    STG_SQL.write_text(before + sql_block(cat) + after, encoding="utf-8")


def sql_problems(cat: dict) -> list[str]:
    _, block, _ = _split_sql(STG_SQL.read_text(encoding="utf-8"))
    if block != sql_block(cat):
        return [f"{STG_SQL.name} exercise map is out of step with the catalogue; "
                "run: python scripts/sync_exercises.py sql"]
    return []


def problems(cat: dict, programme: str | None = None) -> list[str]:
    errs = []
    names = catalogue_names(cat)
    seen = set()
    for n in names:
        if n.lower() in seen:
            errs.append(f"duplicate exercise: {n!r}")
        seen.add(n.lower())
        if ";" in n:
            errs.append(f"{n!r} contains ';', which deploy_views.py would split the SQL on")
        if "/" in n:
            errs.append(f"{n!r} contains '/', which breaks /api/charts/{{exercise_group}}")
        if initcap(n) != n:
            errs.append(f"{n!r} changes under INITCAP() to {initcap(n)!r}; logged rows would not match")
        if n != clean(n):
            errs.append(f"{n!r} has stray whitespace")
    by_key: dict[str, str] = {initcap(n): n for n in names}
    for k, v in cat.get("aliases", {}).items():
        if v.lower() not in seen:
            errs.append(f"alias {k!r} points at {v!r}, which is not in the catalogue")
        if ";" in k:
            errs.append(f"alias {k!r} contains ';', which deploy_views.py would split the SQL on")
        key = initcap(clean(k))
        if by_key.get(key, v) != v:
            errs.append(f"alias {k!r} -> {v!r} clashes with {by_key[key]!r} once BigQuery INITCAPs it")
        by_key.setdefault(key, v)
    lifts = {l.lower() for l in cat.get("one_rm_lifts", [])}
    for k, v in cat.get("one_rm_base", {}).items():
        if k.lower() not in seen:
            errs.append(f"one_rm_base key {k!r} is not in the catalogue")
        if v.lower() not in lifts and v.lower() not in seen:
            errs.append(f"one_rm_base {k!r} -> {v!r}, which is neither a 1RM lift nor a catalogue exercise")
    for k, lifts_for in cat.get("one_rm_reference", {}).items():
        if k.lower() not in seen:
            errs.append(f"one_rm_reference key {k!r} is not in the catalogue")
        for v in lifts_for:
            if v.lower() not in lifts and v.lower() not in seen:
                errs.append(f"one_rm_reference {k!r} -> {v!r}, which is neither a 1RM lift nor a catalogue exercise")
    for c in cat["categories"]:
        if not c.get("label") or not c.get("exercises"):
            errs.append(f"category {c.get('label')!r} is empty or unlabeled")
        if "kind" in c and c["kind"] not in KINDS:
            errs.append(f"category {c.get('label')!r} has unknown kind {c['kind']!r}")
    if programme:
        for n in diff(programme)["new"]:
            errs.append(f"programme exercise not in catalogue: {n!r}")
    return errs


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in {"diff", "apply", "validate", "extract", "sql"}:
        print(__doc__)
        return 2
    cmd, args = argv[0], argv[1:]
    if cmd == "extract":
        print(json.dumps(extract(args[0]), indent=2))
    elif cmd == "diff":
        print(json.dumps(diff(args[0]), indent=2))
    elif cmd == "apply":
        print(json.dumps({"added": apply(args[0], args[1])}, indent=2))
    elif cmd == "sql":
        write_sql(load())
        print(f"Wrote exercise map to {STG_SQL}")
    else:
        cat = load()
        errs = problems(cat, args[0] if args else None) + sql_problems(cat)
        for e in errs:
            print("FAIL", e)
        print("OK" if not errs else f"{len(errs)} problem(s)")
        return 1 if errs else 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
