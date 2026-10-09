from datetime import date
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "code"))

import main  # noqa: E402
import operations  # noqa: E402


class Task2PureHelperTests(unittest.TestCase):
    def test_resolve_vessel_trims_and_casefolds(self):
        vessels = [{"vessel_id": "VSL-002", "name": "Nordic Relay"}]
        self.assertEqual(
            operations.resolve_vessel("  nordic relay  ", vessels),
            vessels[0],
        )

    def test_unknown_vessel_returns_none(self):
        self.assertIsNone(operations.resolve_vessel("Unknown", []))

    def test_reference_date_accepts_real_iso_date(self):
        self.assertEqual(
            operations.parse_reference_date("2026-10-18"),
            date(2026, 10, 18),
        )

    def test_reference_date_rejects_wrong_shape_and_impossible_day(self):
        for value in ("18-10-2026", "2026/10/18", "2026-02-30", "20261018"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    operations.parse_reference_date(value)

    def test_select_call_is_inclusive_and_uses_call_id_tie_break(self):
        calls = [
            {
                "call_id": "HFL-LATER",
                "vessel_id": "VSL-002",
                "arrival_date": "2026-10-19",
            },
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
                "call_id": "HFL-EARLIER",
                "vessel_id": "VSL-002",
                "arrival_date": "2026-10-17",
            },
            {
                "call_id": "HFL-OTHER",
                "vessel_id": "VSL-003",
                "arrival_date": "2026-10-18",
            },
            {
                "call_id": "HFL-BAD",
                "vessel_id": "VSL-002",
                "arrival_date": "2026-02-30",
            },
        ]
        selected = operations.select_call(calls, "VSL-002", date(2026, 10, 18))
        self.assertEqual(selected["call_id"], "HFL-A-TIE")

    def test_select_call_returns_none_when_no_valid_upcoming_call(self):
        calls = [
            {
                "call_id": "HFL-OLD",
                "vessel_id": "VSL-002",
                "arrival_date": "2026-01-01",
            }
        ]
        self.assertIsNone(
            operations.select_call(calls, "VSL-002", date(2026, 10, 18))
        )

    def test_manifest_uses_record_ids_and_report_preserves_manifest_order(self):
        vessel = {"vessel_id": "VSL-002", "name": "Nordic Relay"}
        call = {
            "call_id": "HFL-GOT-2048",
            "vessel_id": "VSL-002",
            "arrival_date": "2026-10-18",
        }
        manifests = [
            {
                "call_id": "HFL-GOT-2048",
                "vessel_id": "VSL-002",
                "shipment_ids": ["SHP-1051", "SHP-1042"],
                "event_codes": [],
            }
        ]
        shipments = [
            {
                "shipment_id": "SHP-1042",
                "customer": "Norra MedTech AB",
                "destination": "GOT",
                "priority": "STANDARD",
                "weight_kg": 860.0,
                "cargo_type": "REFRIGERATED",
            }
        ]

        manifest = operations.find_manifest(manifests, call)
        report = operations.build_manifest_report(
            vessel,
            call,
            manifest,
            operations.index_shipments(shipments),
        )

        self.assertEqual(
            [line["shipment_id"] for line in report["lines"]],
            ["SHP-1051", "SHP-1042"],
        )
        self.assertFalse(report["lines"][0]["resolved"])
        self.assertEqual(report["lines"][1]["cargo_type"], "REFRIGERATED")
        self.assertEqual(report["declared"], 2)
        self.assertEqual(report["resolved_weight"], 860.0)
        self.assertEqual(report["missing"], 1)

    def test_report_defaults_missing_optional_flags_and_cargo_type(self):
        vessel = {"vessel_id": "VSL-002", "name": "Nordic Relay"}
        call = {
            "call_id": "HFL-GOT-2048",
            "vessel_id": "VSL-002",
            "arrival_date": "2026-10-18",
        }
        manifest = {
            "call_id": "HFL-GOT-2048",
            "vessel_id": "VSL-002",
            "shipment_ids": ["SHP-1042"],
            "event_codes": [],
        }
        shipments = [
            {
                "shipment_id": "SHP-1042",
                "customer": "Norra MedTech AB",
                "destination": "GOT",
                "priority": "STANDARD",
                "weight_kg": 860.0,
            }
        ]

        report = operations.build_manifest_report(
            vessel,
            call,
            manifest,
            operations.index_shipments(shipments),
        )

        line = report["lines"][0]
        self.assertFalse(line["hazardous"])
        self.assertFalse(line["temperature_controlled"])
        self.assertEqual(line["cargo_type"], "NOT PROVIDED")


class Task2InteractionTests(unittest.TestCase):
    vessels = [{"vessel_id": "VSL-002", "name": "Nordic Relay"}]
    calls = [
        {
            "call_id": "HFL-GOT-2048",
            "vessel_id": "VSL-002",
            "port_code": "GOT",
            "arrival_date": "2026-10-18",
        }
    ]
    shipments = []

    def run_service(self, answers, calls=None, manifests=None):
        prompts = []
        output = []
        answers = iter(answers)

        def input_fn(prompt):
            prompts.append(prompt)
            return next(answers)

        with patch("builtins.input", side_effect=input_fn):
            main.inspect_manifest(
                self.vessels,
                self.calls if calls is None else calls,
                [] if manifests is None else manifests,
                self.shipments,
                output_fn=output.append,
            )
        return prompts, output

    def test_unknown_vessel_prints_exact_error_and_skips_date_prompt(self):
        prompts, output = self.run_service(["Unknown"])

        self.assertEqual(output, ["Vessel not found."])
        self.assertEqual(prompts, ["Vessel name: "])

    def test_invalid_date_prints_exact_error_and_repeats_only_date_prompt(self):
        old_calls = [
            {
                "call_id": "HFL-OLD",
                "vessel_id": "VSL-002",
                "port_code": "GOT",
                "arrival_date": "2026-01-01",
            }
        ]
        prompts, output = self.run_service(
            ["Nordic Relay", "2026/10/18", "2026-10-18"],
            calls=old_calls,
        )

        self.assertEqual(
            output,
            ["Error - Date must use YYYY-MM-DD.", "No upcoming port calls found."],
        )
        self.assertEqual(
            prompts,
            [
                "Vessel name: ",
                "Reference date (YYYY-MM-DD): ",
                "Reference date (YYYY-MM-DD): ",
            ],
        )

    def test_no_upcoming_call_prints_exact_error(self):
        old_calls = [
            {
                "call_id": "HFL-OLD",
                "vessel_id": "VSL-002",
                "port_code": "GOT",
                "arrival_date": "2026-01-01",
            }
        ]

        prompts, output = self.run_service(
            ["Nordic Relay", "2026-10-18"],
            calls=old_calls,
        )

        self.assertEqual(output, ["No upcoming port calls found."])
        self.assertEqual(
            prompts,
            ["Vessel name: ", "Reference date (YYYY-MM-DD): "],
        )

    def test_unavailable_manifest_prints_exact_error(self):
        prompts, output = self.run_service(["Nordic Relay", "2026-10-18"])

        self.assertEqual(output, ["Manifest unavailable."])
        self.assertEqual(
            prompts,
            ["Vessel name: ", "Reference date (YYYY-MM-DD): "],
        )
