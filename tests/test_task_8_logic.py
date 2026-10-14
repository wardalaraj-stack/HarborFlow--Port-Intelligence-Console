
from pathlib import Path
import sys
from datetime import date

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "code")
)

import operations


def test_upcoming_calls_sort_and_skip_invalid_dates():
    calls = [
        {"vessel_id": "V1", "call_id": "C", "arrival_date": "2026-10-20"},
        {"vessel_id": "V1", "call_id": "B", "arrival_date": "2026-10-14"},
        {"vessel_id": "V1", "call_id": "A", "arrival_date": "2026-10-14"},
        {"vessel_id": "V1", "call_id": "OLD", "arrival_date": "2026-10-13"},
        {"vessel_id": "V1", "call_id": "BAD", "arrival_date": "2026-02-30"},
        {"vessel_id": "V2", "call_id": "OTHER", "arrival_date": "2026-10-15"},
    ]

    upcoming, invalid = operations.select_upcoming_calls(
        calls, "V1", date(2026, 10, 14)
    )

    assert [call["call_id"] for call in upcoming] == ["A", "B", "C"]
    assert invalid == [(6, "2026-02-30")]


def test_weather_lookup_uses_port_and_date():
    weather = [
        {
            "port_code": "GOT",
            "date": "2026-10-14",
            "wind_kmh": "48",
            "precipitation_mm": "3",
            "wave_height_m": "2.7",
        },
        {
            "port_code": "GOT",
            "date": "2026-10-15",
            "wind_kmh": "10",
            "precipitation_mm": "0",
            "wave_height_m": "0.5",
        },
        {
            "port_code": "OSL",
            "date": "2026-10-14",
            "wind_kmh": "20",
            "precipitation_mm": "1",
            "wave_height_m": "1.0",
        },
    ]

    lookup, malformed = operations.build_weather_lookup(weather)

    assert malformed == []
    assert len(lookup) == 3
    assert lookup[("GOT", "2026-10-14")]["wind_kmh"] == 48
    assert lookup[("GOT", "2026-10-15")]["wind_kmh"] == 10
    assert lookup[("OSL", "2026-10-14")]["wind_kmh"] == 20


def test_invalid_weather_row_is_skipped():
    weather = [
        {
            "port_code": "GOT",
            "date": "2026-10-14",
            "wind_kmh": "invalid",
            "precipitation_mm": "3",
            "wave_height_m": "2.7",
        },
        {
            "port_code": "OSL",
            "date": "2026-10-14",
            "wind_kmh": "20",
            "precipitation_mm": "1",
            "wave_height_m": "1.0",
        },
    ]

    lookup, malformed = operations.build_weather_lookup(weather)

    assert len(malformed) == 1
    assert malformed[0][0] == 2
    assert ("GOT", "2026-10-14") not in lookup
    assert ("OSL", "2026-10-14") in lookup
