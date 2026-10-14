"""Automated tests for HarborFlow incident search."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from text_tools import normalize_words
from operations import build_incident_index, search_incident_index


# Task 9 - Search Incident Reports | Tests by Mado Sallom

def sample_incidents():
    return {
        "INC-119": {
            "title": "Reefer transfer delayed",
            "report": "Reefer transfer delay, delay!"
        },
        "INC-087": {
            "title": "Gate congestion delay",
            "report": "Gate congestion delay."
        },
        "INC-102": {
            "title": "Reefer temperature deviation",
            "report": "Reefer temperature deviation."
        }
    }


def test_normalization():
    assert normalize_words("Gate, DELAY! Gate.") == [
        "gate", "delay", "gate"
    ]


def test_index_does_not_duplicate_incident_ids():
    cache = build_incident_index(sample_incidents())

    assert cache["index"]["delay"] == ["INC-087", "INC-119"]


def test_index_is_sorted():
    cache = build_incident_index(sample_incidents())

    assert list(cache["index"]) == sorted(cache["index"])
    assert list(cache["titles"]) == sorted(cache["titles"])

    for ids in cache["index"].values():
        assert ids == sorted(set(ids))


def test_search_ranking():
    cache = build_incident_index(sample_incidents())
    results = search_incident_index(cache, "reefer delay")

    assert [item["incident_id"] for item in results] == [
        "INC-119", "INC-087", "INC-102"
    ]

    assert [item["score"] for item in results] == [2, 1, 1]


def test_repeated_query_words():
    cache = build_incident_index(sample_incidents())

    assert search_incident_index(
        cache, "reefer reefer delay"
    ) == search_incident_index(cache, "reefer delay")


def test_no_matches():
    cache = build_incident_index(sample_incidents())

    assert search_incident_index(cache, "unmatchedword") == []


def test_titles_come_from_cache():
    cache = build_incident_index(sample_incidents())
    cache["titles"]["INC-119"] = "Cached title"

    results = search_incident_index(cache, "reefer")

    matching = next(
        item for item in results
        if item["incident_id"] == "INC-119"
    )

    assert matching["title"] == "Cached title"

def test_cache_save_and_load(tmp_path):
    import data_access

    path = tmp_path / "incident-index.json"
    cache = build_incident_index(sample_incidents())

    data_access.save_incident_index(cache, path)

    assert data_access.load_incident_index(path) == cache


def test_missing_cache_returns_none(tmp_path):
    import data_access

    path = tmp_path / "missing-index.json"

    assert data_access.load_incident_index(path) is None


def test_corrupt_cache_returns_none(tmp_path):
    import data_access

    path = tmp_path / "incident-index.json"
    path.write_text("{invalid json", encoding="utf-8")

    assert data_access.load_incident_index(path) is None


def test_stale_cache_returns_none(tmp_path, monkeypatch):
    import os
    import data_access

    incidents_dir = tmp_path / "incidents"
    incidents_dir.mkdir()

    incident_file = incidents_dir / "inc-001.json"
    incident_file.write_text(
        '{"incident_id": "INC-001"}',
        encoding="utf-8"
    )

    cache_path = tmp_path / "incident-index.json"
    cache = build_incident_index(sample_incidents())

    data_access.save_incident_index(cache, cache_path)

    old_time = incident_file.stat().st_mtime - 100
    os.utime(cache_path, (old_time, old_time))

    monkeypatch.setattr(data_access, "INCIDENTS_DIR", incidents_dir)

    assert data_access.load_incident_index(cache_path) is None


def test_cache_rejects_missing_titles(tmp_path):
    import json
    import data_access

    path = tmp_path / "incident-index.json"

    invalid_cache = {
        "index": {
            "delay": ["INC-999"]
        },
        "titles": {
            "INC-087": "Gate congestion delay"
        }
    }

    path.write_text(
        json.dumps(invalid_cache),
        encoding="utf-8"
    )

    assert data_access.load_incident_index(path) is None


def test_invalid_index_word_returns_none(tmp_path):
    import json
    import data_access

    path = tmp_path / "incident-index.json"

    invalid_cache = {
        "index": {"DELAY!": ["INC-087"]},
        "titles": {"INC-087": "Gate congestion delay"}
    }

    path.write_text(
        json.dumps(invalid_cache),
        encoding="utf-8"
    )

    assert data_access.load_incident_index(path) is None


def test_invalid_cache_is_rebuilt(monkeypatch):
    import operations

    incidents = {
        "INC-087": {
            "title": "Gate congestion delay",
            "report": "Gate congestion delay."
        }
    }

    saved = []

    monkeypatch.setattr(
        operations.data_access,
        "load_incident_index",
        lambda: None
    )

    monkeypatch.setattr(
        operations.data_access,
        "load_incidents",
        lambda: (incidents, [])
    )

    monkeypatch.setattr(
        operations.data_access,
        "save_incident_index",
        lambda cache: saved.append(cache)
    )

    result = operations.get_incident_search_cache()

    assert result == operations.build_incident_index(incidents)
    assert saved == [result]