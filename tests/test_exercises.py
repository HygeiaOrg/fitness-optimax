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


def test_catalogue_is_valid():
    assert sx.problems(sx.load()) == []


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
    assert d["known"]["SA Row"] == "Single Arm Row"
    assert d["known"]["back squat"] == "Back Squat"


def test_apply_adds_exercise_alias_and_category(tmp_path, monkeypatch):
    cat_path = tmp_path / "exercises.json"
    cat_path.write_text(sx.CATALOGUE.read_text())
    monkeypatch.setattr(sx, "CATALOGUE", cat_path)
    p = tmp_path / "prog.xlsx"
    make_programme(p, {"Wk1": [("Zercher Squat", 3), ("Farmers Carry", 3), ("SA Row", 3)]})
    mapping = tmp_path / "map.json"
    mapping.write_text(json.dumps({
        "Zercher Squat": {"name": "Zercher Squat", "category": "Squats & Legs"},
        "Farmers Carry": {"name": "Farmer Carry", "category": "Strongman", "new_category": True},
    }))
    added = sx.apply(p, mapping)
    assert added == ["Farmer Carry", "Zercher Squat"]
    cat = sx.load()
    labels = [c["label"] for c in cat["categories"]]
    assert labels.index("Strongman") == labels.index("General") - 1
    assert cat["aliases"]["Farmers Carry"] == "Farmer Carry"
    assert sx.problems(cat, str(p)) == []


def test_apply_refuses_unmapped(tmp_path, monkeypatch):
    cat_path = tmp_path / "exercises.json"
    cat_path.write_text(sx.CATALOGUE.read_text())
    monkeypatch.setattr(sx, "CATALOGUE", cat_path)
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
    cat_path = tmp_path / "exercises.json"
    cat_path.write_text(sx.CATALOGUE.read_text())
    monkeypatch.setattr(sx, "CATALOGUE", cat_path)
    p = tmp_path / "prog.xlsx"
    make_programme(p, {"Wk1": rows})
    m = tmp_path / "map.json"
    m.write_text(json.dumps(mapping))
    return cat_path, p, m


def test_apply_refuses_unknown_category(tmp_path, monkeypatch):
    cat_path, p, m = _scratch(tmp_path, monkeypatch, [("Zercher Squat", 3)],
                              {"Zercher Squat": {"name": "Zercher Squat", "category": "Squats and Legs"}})
    before = cat_path.read_text()
    with pytest.raises(SystemExit):
        sx.apply(p, m)
    assert cat_path.read_text() == before


def test_apply_refuses_invalid_name_without_writing(tmp_path, monkeypatch):
    cat_path, p, m = _scratch(tmp_path, monkeypatch, [("Tall Snatch", 3)],
                              {"Tall Snatch": {"name": "Tall/High Snatch", "category": "Olympic Lifts"}})
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


def test_apply_records_one_rm_base(tmp_path, monkeypatch):
    cat_path, p, m = _scratch(tmp_path, monkeypatch, [("Tall Snatch", 3)],
                              {"Tall Snatch": {"name": "Tall Snatch", "category": "Olympic Lifts",
                                               "one_rm_base": "Snatch"}})
    sx.apply(p, m)
    assert sx.load()["one_rm_base"]["Tall Snatch"] == "Snatch"
