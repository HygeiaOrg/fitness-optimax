"""Tests for the exercise catalogue and the programme sync script."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import sync_exercises as sx  # noqa: E402

openpyxl = pytest.importorskip("openpyxl")


def make_programme(path, rows_by_sheet):
    """Write a workbook laid out like the NTB programme: an Exercise header,
    then exercise rows with numeric sets, plus note rows that must be ignored."""
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for title, rows in rows_by_sheet.items():
        ws = wb.create_sheet(title)
        ws["A1"], ws["B1"] = "`", "North Tyneside Barbells"
        ws["B6"], ws["C6"], ws["D6"] = "Exercise", "sets", "reps"
        # A second session block further right, as in the real sheet.
        ws["K6"], ws["L6"] = "Exercise", "sets"
        r = 7
        for name, sets in rows:
            ws.cell(r, 2, name)
            ws.cell(r, 3, sets)
            r += 1
        ws.cell(r, 3, "Only hit singles if working sets go well")  # note row
        ws.cell(7, 11, "Front Squat ")
        ws.cell(7, 12, 4)
    wb.save(path)


def _sandbox(tmp_path, monkeypatch):
    """Point the script at scratch copies of the catalogue and the staging SQL."""
    cat_path = tmp_path / "exercises.json"
    cat_path.write_text(sx.CATALOGUE.read_text())
    sql_path = tmp_path / "01_stg_workouts.sql"
    sql_path.write_text(sx.STG_SQL.read_text())
    monkeypatch.setattr(sx, "CATALOGUE", cat_path)
    monkeypatch.setattr(sx, "STG_SQL", sql_path)
    return cat_path, sql_path


def test_catalogue_is_valid():
    cat = sx.load()
    assert sx.problems(cat) == []
    assert sx.sql_problems(cat) == []


def test_only_olympic_lifts_and_muscle_groups():
    cat = sx.load()
    kinds = {c["label"]: c["kind"] for c in cat["categories"]}
    assert set(kinds.values()) == {"olympic", "muscle_group"}
    olympic = [e for c in cat["categories"] if c["kind"] == "olympic" for e in c["exercises"]]
    assert olympic[:2] == ["Snatch", "Clean & Jerk"]
    assert {"Hang Snatch", "Power Clean"} <= set(olympic)
    # Accessories are logged under the muscle group from the original sheet.
    assert "Back Squat" not in sx.catalogue_names(cat)
    assert sx.resolve("Back Squat", cat) == "Leg, Quads"
    assert sx.resolve("SA Row", cat) == "Upper Body, Lat"


def test_sql_map_rolls_sheet_history_up():
    pairs = dict(sx.exercise_map(sx.load()))
    # Values as the sheet holds them, after BigQuery INITCAP.
    assert pairs["Leg, Quads"] == "Leg, Quads"
    assert pairs["Olympic, Clean And Jerk"] == "Clean & Jerk"
    assert pairs["Power, Deadlift (Inc Trap Bar)"] == "Power, Deadlift (Inc Trap Bar)"
    assert pairs["Bench Press"] == "Upper Body, Chest"
    assert "Rdl\\'s" in sx.sql_block(sx.load())


def test_sql_drift_is_flagged(tmp_path, monkeypatch):
    _, sql_path = _sandbox(tmp_path, monkeypatch)
    cat = sx.load()
    cat["aliases"]["Goblet Squat"] = "Leg, Quads"
    assert sx.sql_problems(cat)
    sx.write_sql(cat)
    assert sx.sql_problems(cat) == []
    assert "'Goblet Squat' AS raw_name, 'Leg, Quads'" in sql_path.read_text()


def test_initcap_matches_bigquery():
    assert sx.initcap("hang power clean + jerk") == "Hang Power Clean + Jerk"
    assert sx.initcap("CLEAN & JERK") == "Clean & Jerk"
    assert sx.initcap("SL RDL") == "Sl Rdl"


def test_extract_skips_notes_and_cleans_whitespace(tmp_path):
    p = tmp_path / "prog.xlsx"
    make_programme(p, {"Wk1": [("Snatch", 5), ("Power  Snatch ", 3), ("upto 85%", "x")]})
    assert sx.extract(p) == ["Front Squat", "Power Snatch", "Snatch"]


def test_diff_uses_aliases_and_case(tmp_path):
    p = tmp_path / "prog.xlsx"
    make_programme(p, {"Wk1": [("SA Row", 3), ("back squat", 4), ("Zercher Squat", 3)]})
    d = sx.diff(p)
    assert d["new"] == ["Zercher Squat"]
    assert d["known"]["SA Row"] == "Upper Body, Lat"
    assert d["known"]["back squat"] == "Leg, Quads"


def test_apply_maps_accessories_and_adds_derivatives(tmp_path, monkeypatch):
    _, sql_path = _sandbox(tmp_path, monkeypatch)
    p = tmp_path / "prog.xlsx"
    make_programme(p, {"Wk1": [("Zercher Squat", 3), ("Muscle Snatch", 3), ("Farmers Carry", 3), ("SA Row", 3)]})
    mapping = tmp_path / "map.json"
    mapping.write_text(json.dumps({
        "Zercher Squat": {"name": "Leg, Quads", "category": "Legs & Hips"},
        "Muscle Snatch": {"name": "Muscle Snatch", "category": "Olympic Derivatives", "one_rm_base": "Snatch"},
        "Farmers Carry": {"name": "Farmer Carry", "category": "Strongman", "new_category": True,
                          "kind": "muscle_group"},
    }))
    added = sx.apply(p, mapping)
    assert added == ["Farmer Carry", "Muscle Snatch"]
    cat = sx.load()
    assert cat["aliases"]["Zercher Squat"] == "Leg, Quads"
    assert "Zercher Squat" not in sx.catalogue_names(cat)
    assert cat["categories"][-1] == {"label": "Strongman", "kind": "muscle_group", "exercises": ["Farmer Carry"]}
    assert cat["aliases"]["Farmers Carry"] == "Farmer Carry"
    assert sx.problems(cat, str(p)) == []
    assert sx.sql_problems(cat) == []
    assert "'Zercher Squat' AS raw_name, 'Leg, Quads'" in sql_path.read_text()


def test_apply_refuses_unmapped(tmp_path, monkeypatch):
    _sandbox(tmp_path, monkeypatch)
    p = tmp_path / "prog.xlsx"
    make_programme(p, {"Wk1": [("Zercher Squat", 3)]})
    mapping = tmp_path / "map.json"
    mapping.write_text("{}")
    with pytest.raises(SystemExit):
        sx.apply(p, mapping)


def test_validate_flags_bad_names():
    cat = {"categories": [{"label": "X", "exercises": ["Clean/Jerk", "SA Row", "Snatch", "snatch"]}],
           "aliases": {"Foo": "Missing"}}
    errs = "\n".join(sx.problems(cat))
    assert "'/'" in errs and "INITCAP" in errs and "duplicate" in errs and "Missing" in errs


def _scratch(tmp_path, monkeypatch, rows, mapping):
    cat_path, _ = _sandbox(tmp_path, monkeypatch)
    p = tmp_path / "prog.xlsx"
    make_programme(p, {"Wk1": rows})
    m = tmp_path / "map.json"
    m.write_text(json.dumps(mapping))
    return cat_path, p, m


def test_apply_refuses_unknown_category(tmp_path, monkeypatch):
    cat_path, p, m = _scratch(tmp_path, monkeypatch, [("Zercher Squat", 3)],
                              {"Zercher Squat": {"name": "Zercher Squat", "category": "Legs and Hips"}})
    before = cat_path.read_text()
    with pytest.raises(SystemExit):
        sx.apply(p, m)
    assert cat_path.read_text() == before


def test_apply_refuses_invalid_name_without_writing(tmp_path, monkeypatch):
    cat_path, p, m = _scratch(tmp_path, monkeypatch, [("Tall Snatch", 3)],
                              {"Tall Snatch": {"name": "Tall/High Snatch", "category": "Olympic Derivatives"}})
    before = cat_path.read_text()
    with pytest.raises(SystemExit):
        sx.apply(p, m)
    assert cat_path.read_text() == before


def test_validate_flags_bad_one_rm_base():
    cat = {"categories": [{"label": "X", "exercises": ["Snatch", "Hang Snatch"]}],
           "one_rm_lifts": ["Snatch"],
           "one_rm_base": {"Hang Snatch": "Snatch", "Ghost Lift": "Snatch", "Snatch": "Moon Lift"}}
    errs = "\n".join(sx.problems(cat))
    assert "Ghost Lift" in errs and "Moon Lift" in errs and "Hang Snatch" not in errs


def test_validate_flags_bad_reference_lifts_and_alias_clash():
    cat = {"categories": [{"label": "X", "kind": "muscle_group", "exercises": ["Leg, Quads", "Arms, Biceps"]},
                          {"label": "Y", "kind": "cardio", "exercises": ["Row"]}],
           "one_rm_lifts": ["Back Squat"],
           "one_rm_reference": {"Leg, Quads": ["Back Squat", "Moon Squat"], "Ghost Group": ["Back Squat"]},
           "aliases": {"curls": "Arms, Biceps", "CURLS": "Leg, Quads", "Curl; Hammer": "Arms, Biceps"}}
    errs = "\n".join(sx.problems(cat))
    assert "';'" in errs
    assert "Moon Squat" in errs and "Ghost Group" in errs and "'cardio'" in errs and "clashes" in errs


def test_apply_records_one_rm_base(tmp_path, monkeypatch):
    cat_path, p, m = _scratch(tmp_path, monkeypatch, [("Tall Snatch", 3)],
                              {"Tall Snatch": {"name": "Tall Snatch", "category": "Olympic Derivatives",
                                               "one_rm_base": "Snatch"}})
    sx.apply(p, m)
    assert sx.load()["one_rm_base"]["Tall Snatch"] == "Snatch"
