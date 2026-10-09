from datetime import date
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "code"))

from operations import (  # noqa: E402
    build_manifest_report,
    find_manifest,
    index_shipments,
    parse_reference_date,
    resolve_vessel,
    select_call,
)


class Task2PureHelperTests(unittest.TestCase):
    def test_resolve_vessel_trims_and_casefolds(self):
        vessels = [{"vessel_id": "VSL-002", "name": "Nordic Relay"}]
        self.assertEqual(
            resolve_vessel("  nordic relay  ", vessels),
            vessels[0],
        )

    def test_unknown_vessel_returns_none(self):
        self.assertIsNone(resolve_vessel("Unknown", []))

    def test_reference_date_accepts_real_iso_date(self):
        self.assertEqual(parse_reference_date("2026-10-18"), date(2026, 10, 18))

    def test_reference_date_rejects_wrong_shape_and_impossible_day(self):
        for value in ("18-10-2026", "2026/10/18", "2026-02-30", "20261018"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_reference_date(value)

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
        selected = select_call(calls, "VSL-002", date(2026, 10, 18))
        self.assertEqual(selected["call_id"], "HFL-A-TIE")

    def test_select_call_returns_none_when_no_valid_upcoming_call(self):
        calls = [
            {
                "call_id": "HFL-OLD",
                "vessel_id": "VSL-002",
                "arrival_date": "2026-01-01",
            }
        ]
        self.assertIsNone(select_call(calls, "VSL-002", date(2026, 10, 18)))

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

        manifest = find_manifest(manifests, call)
        report = build_manifest_report(vessel, call, manifest, index_shipments(shipments))

        self.assertEqual(
            [line["shipment_id"] for line in report["lines"]],
            ["SHP-1051", "SHP-1042"],
        )
        self.assertFalse(report["lines"][0]["resolved"])
        self.assertEqual(report["lines"][1]["cargo_type"], "REFRIGERATED")
        self.assertEqual(report["declared"], 2)
        self.assertEqual(report["resolved_weight"], 860.0)
        self.assertEqual(report["missing"], 1)
