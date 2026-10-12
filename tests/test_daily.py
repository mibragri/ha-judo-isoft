"""Tests for the daily consumption derived from the total counter.

Run with: python -m pytest tests/
The module under test has no Home Assistant imports, so it is loaded by path.
"""
import importlib.util
import sys
from pathlib import Path

_PATH = Path(__file__).parent.parent / "custom_components" / "judo" / "daily.py"
_SPEC = importlib.util.spec_from_file_location("judo_daily", _PATH)
daily = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = daily
_SPEC.loader.exec_module(daily)


def run(readings, meter=None):
    """Feed (day, counter) readings and return the meter after the last one."""
    for day, total_l in readings:
        meter = daily.advance(meter, day, total_l)
    return meter


def test_first_reading_starts_the_day_at_zero():
    assert run([("2026-10-12", 5000)]).litres == 0


def test_same_day_readings_count_up():
    assert run([("2026-10-12", 5000), ("2026-10-12", 5025), ("2026-10-12", 5040)]).litres == 40


def test_water_used_across_midnight_counts_for_the_new_day():
    # Last reading of the old day at 5150, first of the new day at 5190: the 40 L in between
    # must not be lost.
    meter = run([("2026-10-12", 5000), ("2026-10-12", 5150), ("2026-10-13", 5190)])
    assert meter.date == "2026-10-13"
    assert meter.litres == 40


def test_daily_values_add_up_to_the_counter_delta():
    readings = [("d1", 100), ("d1", 180), ("d2", 195), ("d2", 300), ("d4", 420), ("d4", 421)]
    meter, per_day = None, {}
    for day, total_l in readings:
        meter = daily.advance(meter, day, total_l)
        per_day[day] = meter.litres
    assert sum(per_day.values()) == 421 - 100


def test_day_change_without_consumption_starts_at_zero():
    assert run([("d1", 5000), ("d1", 5150), ("d2", 5150)]).litres == 0


def test_single_low_reading_is_ignored():
    meter = run([("d1", 202203299), ("d1", 202203339), ("d1", 0)])
    assert meter.litres == 40
    assert daily.advance(meter, "d1", 202203345).litres == 46


def test_repeated_low_reading_is_a_counter_reset_and_keeps_todays_count():
    meter = run([("d1", 1000), ("d1", 1150), ("d1", 3), ("d1", 5)])
    assert meter.litres == 150
    assert daily.advance(meter, "d1", 12).litres == 157


def test_low_reading_right_after_midnight_does_not_lose_the_gap():
    meter = run([("d1", 5000), ("d1", 5150), ("d2", 0)])
    assert (meter.date, meter.litres) == ("d2", 0)
    assert daily.advance(meter, "d2", 5190).litres == 40


def test_stored_form_round_trips():
    meter = run([("d1", 1000), ("d1", 1150)])
    assert daily.DayMeter.from_stored(meter.as_stored()) == meter


def test_baseline_written_by_the_first_version_is_taken_over():
    # 0.2.6-dev stored {"date", "total_l"}: the counter value at the start of the day.
    meter = daily.DayMeter.from_stored({"date": "d1", "total_l": 1000})
    assert daily.advance(meter, "d1", 1150).litres == 150


def test_unusable_stored_data_is_dropped():
    for data in (None, [], {"date": "d1"}, {"date": "d1", "base_l": "x", "last_l": 5}, {"date": 5, "base_l": 1, "last_l": 2}):
        assert daily.DayMeter.from_stored(data) is None


def test_a_fresh_count_remembers_when_it_started():
    # Without stored state the count starts now, not at midnight: last_reset must say so,
    # or the statistics would see the value fall within one cycle.
    meter = daily.advance(None, "d1", 1000, started="2026-10-12T15:00:00+02:00")
    assert meter.since == "2026-10-12T15:00:00+02:00"
    assert daily.advance(meter, "d1", 1010, started="2026-10-12T15:06:00+02:00").since == "2026-10-12T15:00:00+02:00"
    assert daily.DayMeter.from_stored(meter.as_stored()) == meter


def test_a_new_day_starts_at_midnight_again():
    meter = daily.advance(None, "d1", 1000, started="2026-10-12T15:00:00+02:00")
    assert daily.advance(meter, "d2", 1010, started="2026-10-13T00:03:00+02:00").since is None
