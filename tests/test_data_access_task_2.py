import json
import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "code"))

from data_access import load_manifests, load_port_calls, load_shipments, load_vessels


class LoaderTests(unittest.TestCase):
    root = Path(__file__).with_name("_task2_loader_fixture")

    def setUp(self):
        if self.root.exists():
            shutil.rmtree(self.root)
        self.root.mkdir()
        self.addCleanup(lambda: shutil.rmtree(self.root, ignore_errors=True))

    def write_json(self, directory, filename, record):
        directory = self.root / directory
        directory.mkdir(exist_ok=True)
        contents = record if isinstance(record, str) else json.dumps(record)
        (directory / filename).write_text(contents, encoding="utf-8")

    def test_malformed_json_is_diagnosed_and_later_files_continue(self):
        self.write_json("vessels", "a-bad.json", '{"vessel_id":')
        self.write_json(
            "vessels",
            "b-good.json",
            {"vessel_id": "VSL-002", "name": "Nordic Relay", "imo": "9471155", "capacity_teu": 1120},
        )

        result = load_vessels(self.root / "vessels")

        self.assertEqual([record["vessel_id"] for record in result.records], ["VSL-002"])
        self.assertEqual(result.diagnostics[0].code, "malformed_json")
        self.assertEqual(result.diagnostics[0].source, str(self.root / "vessels" / "a-bad.json"))

    def test_required_fields_and_types_are_rejected(self):
        self.write_json("vessels", "a-missing.json", {"vessel_id": "VSL-001"})
        self.write_json(
            "vessels",
            "b-bool-capacity.json",
            {"vessel_id": "VSL-002", "name": "Relay", "imo": "1", "capacity_teu": True},
        )
        self.write_json(
            "manifests",
            "c-bad-list.json",
            {"call_id": "CALL-1", "vessel_id": "VSL-001", "shipment_ids": [1], "event_codes": []},
        )
        self.write_json(
            "shipments",
            "d-bad-weight.json",
            {
                "shipment_id": "SHP-1",
                "customer": "Customer",
                "destination": "GOT",
                "priority": "STANDARD",
                "weight_kg": True,
            },
        )

        vessels = load_vessels(self.root / "vessels")
        manifests = load_manifests(self.root / "manifests")
        shipments = load_shipments(self.root / "shipments")

        self.assertEqual(vessels.records, [])
        self.assertEqual(manifests.records, [])
        self.assertEqual(shipments.records, [])
        self.assertTrue(all(d.code == "invalid_record" for d in vessels.diagnostics))
        self.assertEqual(manifests.diagnostics[0].message, "shipment_ids must contain only text values")
        self.assertEqual(shipments.diagnostics[0].message, "weight_kg must be a number")

    def test_files_are_sorted_and_duplicate_identity_is_exact(self):
        # Business-ID duplicate identity is exact; "VSL-2" and "vsl-2" are distinct.
        base = {"name": "First", "imo": "1", "capacity_teu": 1}
        self.write_json("vessels", "z-last.json", {"vessel_id": "VSL-2", **base})
        self.write_json("vessels", "a-first.json", {"vessel_id": "VSL-1", **base})
        self.write_json("vessels", "b-duplicate.json", {"vessel_id": "VSL-1", "name": "Duplicate", "imo": "2", "capacity_teu": 2})
        self.write_json("vessels", "c-case-variant.json", {"vessel_id": "vsl-2", "name": "Case Variant", "imo": "3", "capacity_teu": 3})

        result = load_vessels(self.root / "vessels")

        self.assertEqual([record["vessel_id"] for record in result.records], ["VSL-1", "vsl-2", "VSL-2"])
        self.assertEqual(result.records[0]["name"], "First")
        self.assertEqual([d.code for d in result.diagnostics], ["duplicate_identifier"])
        self.assertIn("VSL-1", result.diagnostics[0].message)

    def test_csv_header_rows_and_source_strings_are_preserved(self):
        calls = self.root / "port_calls.csv"
        calls.write_text(
            "call_id,vessel_id,port_code\n"
            "CALL-1,VSL-1,GOT\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "missing columns: arrival_date"):
            load_port_calls(calls)

        calls.write_text(
            "call_id,vessel_id,port_code,arrival_date\n"
            "CALL-1,VSL-1,GOT,2026-02-30\n"
            ",VSL-2,OSL,2026-11-01\n"
            "CALL-1,VSL-3,CPH,2026-12-01\n",
            encoding="utf-8",
        )
        result = load_port_calls(calls)

        self.assertEqual(result.records[0]["arrival_date"], "2026-02-30")
        self.assertEqual(len(result.diagnostics), 2)
        self.assertEqual(result.diagnostics[0].source, f"{calls}:row 3")
        self.assertEqual(result.diagnostics[0].code, "invalid_row")
        self.assertEqual(result.diagnostics[1].code, "duplicate_identifier")


if __name__ == "__main__":
    unittest.main()
