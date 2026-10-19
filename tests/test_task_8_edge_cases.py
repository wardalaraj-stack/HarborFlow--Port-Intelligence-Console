
from pathlib import Path
from unittest.mock import patch
import sys

# Make the project's code directory importable.
sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "code")
)

import main
import operations
import data_access


def test_task8_vessel_not_found(capsys):
    with (
        patch("builtins.input", side_effect=[
            "Unknown Vessel", "2026-10-14"
        ]),
        patch.object(data_access, "load_vessels", return_value=({}, [])),
        patch.object(data_access, "load_port_calls", return_value=([], [])),
        patch.object(data_access, "load_weather", return_value=([], [])),
        patch.object(
            operations,
            "assess_weather_risk",
            return_value={"status": "vessel_not_found"},
        ),
    ):
        main.run_weather_risk()

    output = capsys.readouterr().out
    assert "Vessel not found." in output


def test_task8_no_upcoming_calls(capsys):
    with (
        patch("builtins.input", side_effect=[
            "Nordic Relay", "2026-10-14"
        ]),
        patch.object(data_access, "load_vessels", return_value=({}, [])),
        patch.object(data_access, "load_port_calls", return_value=([], [])),
        patch.object(data_access, "load_weather", return_value=([], [])),
        patch.object(
            operations,
            "assess_weather_risk",
            return_value={"status": "no_upcoming_calls"},
        ),
    ):
        main.run_weather_risk()

    output = capsys.readouterr().out
    assert "No upcoming port calls found." in output


def test_task8_data_error_is_handled(capsys):
    with (
        patch("builtins.input", side_effect=[
            "Nordic Relay", "2026-10-14"
        ]),
        patch.object(
            data_access,
            "load_vessels",
            side_effect=ValueError("Invalid vessel data"),
        ),
    ):
        main.run_weather_risk()

    output = capsys.readouterr().out
    assert "Error assessing weather risk:" in output
    assert "Invalid vessel data" in output


def test_task8_multiple_calls_displayed(capsys):
    reports = [
        {
            "call": {
                "call_id": "CALL-A",
                "port_code": "GOT",
                "arrival_date": "2026-10-14",
            },
            "forecast": None,
            "recommendations": [],
        },
        {
            "call": {
                "call_id": "CALL-B",
                "port_code": "OSL",
                "arrival_date": "2026-10-15",
            },
            "forecast": None,
            "recommendations": [],
        },
    ]

    with (
        patch("builtins.input", side_effect=[
            "Nordic Relay", "2026-10-14"
        ]),
        patch.object(data_access, "load_vessels", return_value=({}, [])),
        patch.object(data_access, "load_port_calls", return_value=([], [])),
        patch.object(data_access, "load_weather", return_value=([], [])),
        patch.object(
            operations,
            "assess_weather_risk",
            return_value={"status": "ok", "reports": reports},
        ),
    ):
        main.run_weather_risk()

    output = capsys.readouterr().out
   
    assert "Nordic Relay | GOT | 14 October 2026" in output
    assert "Nordic Relay | OSL | 15 October 2026" in output

    assert output.count("Forecast unavailable.") == 2
