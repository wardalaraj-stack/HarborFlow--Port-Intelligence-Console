from contextlib import redirect_stdout
from datetime import date
from io import StringIO
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).parents[1] / "code"))

import main
import operations


class Task2OperationsTests(unittest.TestCase):
    def test_find_vessel_by_name_trims_and_ignores_case(self):
        vessels = {
            "VSL-002": {
                "vessel_id": "VSL-002",
                "name": "Nordic Relay",
                "imo": "9471155",
                "capacity_teu": 1120,
            }
        }

        result = operations.find_vessel_by_name("  nordic relay ", vessels)

        self.assertEqual(result, vessels["VSL-002"])

    def test_select_upcoming_call_uses_date_then_call_id(self):
        calls = [
            {
                "call_id": "HFL-Z-TIE",
                "vessel_id": "VSL-002",
                "arrival_date": "2026-10-18",
            },
            {
                "call_id": "HFL-A-TIE",
                "vessel_id": "VSL-002",
                "arrival_date": "2026-10-18",
            },
            {
                "call_id": "HFL-OLD",
                "vessel_id": "VSL-002",
                "arrival_date": "2026-10-17",
            },
        ]

        result = operations.select_upcoming_call(
            calls,
            "VSL-002",
            date(2026, 10, 18),
        )

        self.assertEqual(result["call_id"], "HFL-A-TIE")

    def test_build_manifest_report_keeps_order_and_counts_missing_shipments(self):
        vessel = {"vessel_id": "VSL-002", "name": "Nordic Relay"}
        call = {
            "call_id": "HFL-GOT-2048",
            "vessel_id": "VSL-002",
            "arrival_date": "2026-10-18",
        }
        manifest = {
            "call_id": "HFL-GOT-2048",
            "vessel_id": "VSL-002",
            "shipment_ids": ["SHP-MISSING", "SHP-1042"],
            "event_codes": [],
        }
        shipments = {
            "SHP-1042": {
                "shipment_id": "SHP-1042",
                "customer": "Norra MedTech AB",
                "weight_kg": 860.0,
            }
        }

        report = operations.build_manifest_report(
            vessel,
            call,
            manifest,
            shipments,
        )

        self.assertEqual(
            [line["shipment_id"] for line in report["lines"]],
            ["SHP-MISSING", "SHP-1042"],
        )
        self.assertEqual(report["resolved_weight"], 860.0)
        self.assertEqual(report["missing"], 1)
        self.assertEqual(report["lines"][1]["cargo_type"], "NOT PROVIDED")


class Task2ServiceTests(unittest.TestCase):
    def test_unknown_vessel_does_not_ask_for_date(self):
        with patch("main.data_access.load_vessels", return_value=({}, [])), \
             patch("main.data_access.load_port_calls", return_value=([], [])), \
             patch("main.data_access.load_manifests", return_value=({}, [])), \
             patch("main.data_access.load_shipments", return_value=({}, [])), \
             patch("builtins.input", side_effect=["Unknown vessel"]) as input_mock:
            output = StringIO()
            with redirect_stdout(output):
                main.run_inspect_manifest()

        self.assertIn("Vessel not found.", output.getvalue())
        self.assertEqual(input_mock.call_count, 1)

    def test_invalid_date_repeats_only_the_date_prompt(self):
        vessels = {
            "VSL-002": {
                "vessel_id": "VSL-002",
                "name": "Nordic Relay",
                "imo": "9471155",
                "capacity_teu": 1120,
            }
        }

        with patch("main.data_access.load_vessels", return_value=(vessels, [])), \
             patch("main.data_access.load_port_calls", return_value=([], [])), \
             patch("main.data_access.load_manifests", return_value=({}, [])), \
             patch("main.data_access.load_shipments", return_value=({}, [])), \
             patch(
                 "builtins.input",
                 side_effect=["Nordic Relay", "2026-02-30", "2026-10-18"],
             ) as input_mock:
            output = StringIO()
            with redirect_stdout(output):
                main.run_inspect_manifest()

        self.assertIn("Error - Date must use YYYY-MM-DD.", output.getvalue())
        self.assertIn("No upcoming port calls found.", output.getvalue())
        self.assertEqual(input_mock.call_count, 3)

    def test_no_upcoming_call_prints_exact_message(self):
        vessels = {
            "VSL-002": {
                "vessel_id": "VSL-002",
                "name": "Nordic Relay",
                "imo": "9471155",
                "capacity_teu": 1120,
            }
        }
        old_calls = [
            {
                "call_id": "HFL-OLD",
                "vessel_id": "VSL-002",
                "port_code": "GOT",
                "arrival_date": "2026-01-01",
            }
        ]

        with patch("main.data_access.load_vessels", return_value=(vessels, [])), \
             patch("main.data_access.load_port_calls", return_value=(old_calls, [])), \
             patch("main.data_access.load_manifests", return_value=({}, [])), \
             patch("main.data_access.load_shipments", return_value=({}, [])), \
             patch("builtins.input", side_effect=["Nordic Relay", "2026-10-18"]):
            output = StringIO()
            with redirect_stdout(output):
                main.run_inspect_manifest()

        self.assertIn("No upcoming port calls found.", output.getvalue())

    def test_service_loads_data_then_prints_missing_shipment(self):
        vessels = {
            "VSL-002": {
                "vessel_id": "VSL-002",
                "name": "Nordic Relay",
                "imo": "9471155",
                "capacity_teu": 1120,
            }
        }
        calls = [
            {
                "call_id": "HFL-GOT-2048",
                "vessel_id": "VSL-002",
                "port_code": "GOT",
                "arrival_date": "2026-10-18",
            }
        ]
        manifests = {
            "HFL-GOT-2048": {
                "call_id": "HFL-GOT-2048",
                "vessel_id": "VSL-002",
                "shipment_ids": ["SHP-MISSING"],
                "event_codes": [],
            }
        }

        with patch("main.data_access.load_vessels", return_value=(vessels, [])), \
             patch("main.data_access.load_port_calls", return_value=(calls, [])), \
             patch("main.data_access.load_manifests", return_value=(manifests, [])), \
             patch("main.data_access.load_shipments", return_value=({}, [])), \
             patch("builtins.input", side_effect=["Nordic Relay", "2026-10-18"]):
            output = StringIO()
            with redirect_stdout(output):
                main.run_inspect_manifest()

        text = output.getvalue()
        self.assertIn("Manifest for Nordic Relay | Call HFL-GOT-2048 | 18 October 2026", text)
        self.assertIn("1. SHP-MISSING | MISSING RECORD", text)
        self.assertIn("Resolved weight: 0.00 kg", text)


if __name__ == "__main__":
    unittest.main()
