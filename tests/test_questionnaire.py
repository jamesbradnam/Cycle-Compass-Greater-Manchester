import builtins

import pytest

from src.questionnaire import _ask_choice, _ask_multi, _ask_yes_no


def _feed(monkeypatch, answers):
    responses = iter(answers)
    monkeypatch.setattr(builtins, "input", lambda _prompt="": next(responses))


def test_ask_choice_accepts_valid_first_try(monkeypatch):
    _feed(monkeypatch, ["manchester"])
    assert _ask_choice("Which borough?", ["manchester", "salford"]) == "manchester"


def test_ask_choice_is_case_insensitive_and_strips_whitespace(monkeypatch):
    _feed(monkeypatch, ["  MANCHESTER  "])
    assert _ask_choice("Which borough?", ["manchester", "salford"]) == "manchester"


def test_ask_choice_retries_on_invalid_input(monkeypatch, capsys):
    _feed(monkeypatch, ["nowhereville", "salford"])
    result = _ask_choice("Which borough?", ["manchester", "salford"])
    assert result == "salford"
    assert "Please choose one of" in capsys.readouterr().out


def test_ask_multi_parses_comma_separated_values(monkeypatch):
    _feed(monkeypatch, ["commuting, leisure"])
    assert _ask_multi("Purpose?", ["commuting", "leisure", "errands"]) == [
        "commuting",
        "leisure",
    ]


def test_ask_multi_rejects_unknown_value_and_retries(monkeypatch, capsys):
    _feed(monkeypatch, ["commuting,scootering", "errands"])
    result = _ask_multi("Purpose?", ["commuting", "leisure", "errands"])
    assert result == ["errands"]
    assert "Please choose one or more of" in capsys.readouterr().out


def test_ask_multi_rejects_empty_input(monkeypatch):
    _feed(monkeypatch, ["", "leisure"])
    assert _ask_multi("Purpose?", ["commuting", "leisure", "errands"]) == ["leisure"]


@pytest.mark.parametrize(
    "raw,expected",
    [("y", True), ("yes", True), ("n", False), ("no", False), ("Y", True)],
)
def test_ask_yes_no_parses_variants(monkeypatch, raw, expected):
    _feed(monkeypatch, [raw])
    assert _ask_yes_no("Employed?") is expected


def test_ask_yes_no_retries_on_invalid_input(monkeypatch, capsys):
    _feed(monkeypatch, ["maybe", "n"])
    assert _ask_yes_no("Employed?") is False
    assert "Please answer y or n" in capsys.readouterr().out
