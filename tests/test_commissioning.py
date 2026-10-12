"""Tests for the commissioning date the user can set."""
import importlib.util
import sys
from datetime import date
from pathlib import Path

_PATH = Path(__file__).parent.parent / "custom_components" / "judo" / "commissioning.py"
_SPEC = importlib.util.spec_from_file_location("judo_commissioning", _PATH)
commissioning = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = commissioning
_SPEC.loader.exec_module(commissioning)


def test_stored_date_is_read_back():
    assert commissioning.parse_date("2024-03-01") == date(2024, 3, 1)


def test_missing_or_unusable_date_means_not_set():
    for value in (None, "", "01.03.2024", 20240301):
        assert commissioning.parse_date(value) is None


def test_days_in_service_count_from_the_commissioning_date():
    assert commissioning.days_in_service(date(2024, 3, 1), date(2024, 3, 1)) == 0
    assert commissioning.days_in_service(date(2024, 3, 1), date(2025, 3, 1)) == 365


def test_a_date_in_the_future_gives_no_value():
    assert commissioning.days_in_service(date(2030, 1, 1), date(2026, 10, 12)) is None
