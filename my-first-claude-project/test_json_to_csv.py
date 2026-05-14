import csv
import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from json_to_csv import (
    FEEDBACK_URL,
    collect_columns,
    load_json,
    main,
    matches,
    send_feedback,
    write_csv,
)


# --- matches ---

def test_matches_no_filters():
    assert matches({"a": "1"}, [], "all") is True


def test_matches_all_pass():
    assert matches({"a": "1", "b": "2"}, [("a", "1"), ("b", "2")], "all") is True


def test_matches_all_fail():
    assert matches({"a": "1", "b": "x"}, [("a", "1"), ("b", "2")], "all") is False


def test_matches_any_pass():
    assert matches({"a": "1", "b": "x"}, [("a", "1"), ("b", "2")], "any") is True


def test_matches_any_fail():
    assert matches({"a": "z", "b": "x"}, [("a", "1"), ("b", "2")], "any") is False


def test_matches_missing_key_treated_as_empty():
    assert matches({}, [("a", "")], "all") is True


# --- collect_columns ---

def test_collect_columns_single_record():
    assert collect_columns([{"a": 1, "b": 2}]) == ["a", "b"]


def test_collect_columns_union_keys():
    result = collect_columns([{"a": 1}, {"b": 2}])
    assert set(result) == {"a", "b"}


def test_collect_columns_empty():
    assert collect_columns([]) == []


# --- load_json ---

def test_load_json_valid(tmp_path):
    p = tmp_path / "data.json"
    p.write_text('[{"a": 1}]', encoding="utf-8")
    assert load_json(p) == [{"a": 1}]


def test_load_json_file_not_found(tmp_path):
    with pytest.raises(SystemExit, match="見つかりません"):
        load_json(tmp_path / "missing.json")


def test_load_json_invalid_json(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("not json", encoding="utf-8")
    with pytest.raises(SystemExit, match="解析に失敗"):
        load_json(p)


def test_load_json_not_array(tmp_path):
    p = tmp_path / "obj.json"
    p.write_text('{"a": 1}', encoding="utf-8")
    with pytest.raises(SystemExit, match="配列"):
        load_json(p)


# --- write_csv ---

def test_write_csv(tmp_path):
    out = tmp_path / "out.csv"
    write_csv(out, [{"a": "1", "b": "2"}], ["a", "b"])
    reader = csv.DictReader(out.read_text(encoding="utf-8").splitlines())
    rows = list(reader)
    assert rows == [{"a": "1", "b": "2"}]


# --- main (integration) ---

def test_main_basic(tmp_path):
    inp = tmp_path / "data.json"
    inp.write_text('[{"name": "Alice", "status": "active"}]', encoding="utf-8")
    out = tmp_path / "out.csv"
    assert main([str(inp), str(out)]) == 0
    assert out.exists()


def test_main_filter(tmp_path):
    inp = tmp_path / "data.json"
    inp.write_text(
        '[{"name": "Alice", "status": "active"}, {"name": "Bob", "status": "inactive"}]',
        encoding="utf-8",
    )
    out = tmp_path / "out.csv"
    main([str(inp), str(out), "--filter", "status=active"])
    rows = list(csv.DictReader(out.read_text(encoding="utf-8").splitlines()))
    assert len(rows) == 1
    assert rows[0]["name"] == "Alice"


def test_main_missing_args():
    with pytest.raises(SystemExit):
        main([])


# --- feedback ---

def test_send_feedback_prints_url(capsys):
    with patch("webbrowser.open"):
        result = send_feedback()
    captured = capsys.readouterr()
    assert FEEDBACK_URL in captured.out
    assert result == 0


def test_send_feedback_opens_browser():
    with patch("webbrowser.open") as mock_open:
        send_feedback()
    mock_open.assert_called_once_with(FEEDBACK_URL)


def test_main_feedback_flag(capsys):
    with patch("webbrowser.open"):
        result = main(["--feedback"])
    captured = capsys.readouterr()
    assert FEEDBACK_URL in captured.out
    assert result == 0
