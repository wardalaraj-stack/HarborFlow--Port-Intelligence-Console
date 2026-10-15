# HarborFlow — Data and Variable Dictionary

**Status:** Working team reference — review required  
**Basis:** *Data and Variable Dictionary* (team teaching/planning pack, 7 October 2026), official DIT014 Assignment 2 and supplied starter data, plus Task 5 implementation and tests reviewed on 13 October 2026.  
**Scope:** Original T0–T9 information preserved; Task 5 expanded with implementation-specific variables. Other task names and types remain proposals until checked against the actual code.

> This document describes variables used or proposed across HarborFlow. It does not replace [`../dataset/DATA-DICTIONARY.md`](../dataset/DATA-DICTIONARY.md), which defines the source data schema. Uppercase constants are a naming convention, not enforced immutability. Do not put every variable in one shared global file.

## 1. Shared data fields

| Field | Source type | Tasks | Purpose / note |
|---|---|---|---|
| `vessel_id` | `str` | T1, T2, T5, T8 | Join vessels and calls |
| `call_id` | `str` | T2, T3, T5, T7, T8, T9 | Identify call and link manifests/incidents |
| `shipment_id` | `str` | T2, T3, T4 | Identify shipment; `shipment_ids` is an ordered `list[str]` in manifest |
| `name`, `customer`, `destination` | `str` | As applicable | Vessel display, customer matching, destination aggregation |
| `arrival_date`, `date` | ISO date `str` in source | T2, T5, T8 | Convert to `date` before ordering |
| `port_code` | `str` | T2, T5, T8 | Part of weather key |
| `imo` | Source value | T1 | Inventory display; `capacity_teu` is integer capacity |
| `weight_kg` | Number | T2, T3, T4 | Sum or compare; `priority` is `str` |
| `hazardous`, `temperature_controlled` | `bool` | T2, T3 | Absent defaults to `False` |
| `cargo_type` | `str` | T2 | Absent displays `NOT PROVIDED` |
| `event_codes` | `list[str]` | T7 | Ordered events |
| `incident_id`, `title`, `report` | `str` | T6, T9 | Incident identity, display and text |

## 2. Paths and collections

| Name | Proposed type | Purpose |
|---|---|---|
| `DATASET_DIR`, `EXPORTS_DIR` | `Path` | All loaders / generated output |
| `VESSELS_DIR`, `MANIFESTS_DIR`, `SHIPMENTS_DIR`, `INCIDENTS_DIR` | `Path` | JSON directories |
| `PORT_CALLS_PATH`, `WEATHER_PATH` | `Path` | Input CSV files |
| `INCIDENT_INDEX_PATH` | `Path` | T9 cache |
| `CUSTOMER_PROFILES_PATH`, `SANITIZED_DIR` | `Path` | T4 / T6 outputs |
| `records`, `vessels`, `manifests`, `shipments`, `incidents` | `list[dict]` (proposal) | Record collections; actual return shapes must be verified per loader |
| `issues` | `list[dict]` (original proposal) | File and reason diagnostics; `skipped_files = len(issues)` for T1. **Task 5 uses tuple diagnostics**, documented below |
| `record`, `vessel`, `manifest`, `shipment`, `incident` | `dict` | One item |
| `path`, `source_file`, `reader` | `Path`, file object, `DictReader` | Loader locals |
| `required_fields`, `missing_fields` | `tuple[str]`, `list[str]` | Validation |
| `lookup_value` | `str` | Normalized comparison |

The original document marked these names as proposals. Verify names and types against the code before treating them as finalized API contracts.

## 3. Task variables T0–T9

### T0 — Product shell

| Variable | Type | Purpose |
|---|---|---|
| `running` | `bool` | Controls menu |
| `service_choice` | `int` | Selects services 1–10 |
| `raw_choice` | `str` | Input before conversion |

### T1 — Register vessels

| Variable | Type | Purpose |
|---|---|---|
| `sorted_vessels` | `list[dict]` | Sorted vessel list |
| `skipped_files` | `int` | Count of skipped files |

### T2 — Inspect vessel manifest

| Variable | Type | Purpose |
|---|---|---|
| `vessel_name` | `str` | Vessel selected/displayed |
| `reference_date` | `date` | Reference date |
| `selected_call` | `dict \| None` | Selected call |
| `selected_manifest` | `dict \| None` | Selected manifest |
| `resolved_weight` | `float` | Accumulated resolved weight |
| `missing_count` | `int` | Missing links count |
| `declared_count` | `int` | Declared items count |
| `shipment_number` | `int` | Shipment number |

### T3 — Identify priority cargo

| Variable | Type | Purpose |
|---|---|---|
| `call_id` | `str` | Selected call |
| `category`, `reason` | `str` | Classification and rationale |
| `category_counts` | `dict[str, int]` | Counts ordered CONTROLLED, COLD CHAIN, EXPEDITE, STANDARD |

### T4 — Customer operations profile

| Variable | Type | Purpose |
|---|---|---|
| `customer_name` | `str` | Customer selected |
| `matching_shipments` | `list[dict]` | Customer shipments |
| `shipment_count` | `int` | Number of matching shipments |
| `total_weight_kg` | Number | Total; converted to a two-decimal string at CSV output boundary |
| `express_count` | `int` | Express count |
| `destinations` | `set[str]` | Unique destinations |
| `destination_text` | `str` | Destination output |
| `existing_rows` | `list[dict]` | Existing profile rows |
| `profile` | `dict` | Profile data |

### T5 — Find port calls by month

**Original planning variables (preserved):**

| Variable | Type | Purpose |
|---|---|---|
| `month` | `int` | User-selected month (1–12) |
| `call_date` | `datetime.date` | Parsed arrival date |
| `matching_calls` | `list[dict]` | Valid calls in the selected month, sorted for display |
| `vessel_by_id` | `dict[str, dict]` | Vessel lookup keyed by `vessel_id` |

**Additional variables confirmed from `run_port_calls_by_month()` and `collect_month_calls()` shared during Task 5:**

| Variable | Type | Purpose |
|---|---|---|
| `valid_month` | `bool` | Controls month-input retry loop |
| `month_text` | `str` | Raw user input before `int()` conversion |
| `records` | `list[dict]` | Port call records loaded from CSV |
| `issues` | `list[tuple[int, str]]` | CSV loader diagnostics: `(line_number, reason)` |
| `vessel_issues` | List of `(source_file, reason)` tuples | Diagnostics from vessel JSON loader |
| `call_issues` | `list[tuple[str, str]]` | Rejected calls: `(call_id, reason)` |
| `matching_calls` | `list[dict]` | Each item has `call_date`, `vessel_name`, `port_code`, `call_id` |
| `month_names` | `tuple[str, ...]` | English month labels |
| `month_name` | `str` | Label for selected month |
| `date_display` | `str` | Formatted date such as `02 October 2026` |
| `line_number` | `int` | CSV source line from an issue tuple |
| `reason` | `str` | Diagnostic description from an issue tuple |
| `source_file` | Source filename | File identifier from a vessel issue tuple |
| `call_id` | `str` | Call identifier from a rejected call tuple |
| `error` | Exception instance (`FileNotFoundError` or `ValueError`) | Exception caught for service-level error reporting |
| `vessel_id` | `str` | Vessel identifier from port call record |
| `vessel` | `dict` | Resolved vessel record |
| `record` | `dict` | Source port-call row or formatted matching-call record, depending on loop |

**T5 function and collection contracts verified from shared implementation:**

- `data_access.load_port_calls()` returns `(records, issues)` rather than a proposed `LoadResult` object.
- `data_access.load_vessels()` returns `(vessel_by_id, vessel_issues)`.
- `operations.collect_month_calls(month, records, vessel_by_id)` returns `(matching_calls, call_issues)`.
- `matching_calls` entries have four keys: `call_date` (`date`), `vessel_name` (`str`), `port_code` (`str`), and `call_id` (`str`).
- Sort order is `(call_date, vessel_name.casefold(), call_id)`: arrival date first, case-insensitive vessel name second, call ID third.
- Invalid arrival dates are rejected before unknown-vessel lookup, so a row with both problems produces one invalid-date diagnostic.
- File-level failures handled by the service include missing vessel directory / missing CSV, `csv.Error`, and malformed CSV headers (`ValueError`).

**Important diagnostic formats:** Do not treat all `issues` collections as interchangeable dictionaries. T5's CSV loader and collection validation return tuples, with different first fields (`line_number`, `source_file`, `call_id`).

**Task 5 review notes:** These implementation-specific details are based on code pasted during the review session and verified test outputs. Recheck against the final merged branch before marking the document definitive.

### T6 — Sanitize incident report

| Variable | Type | Purpose |
|---|---|---|
| `sorted_incidents` | `list[dict]` | Sorted incidents |
| `incident_number` | `int` | 1-based incident number; Python index is `incident_number - 1` after validating range |
| `selected_incident` | `dict` | Chosen incident |
| `sanitized_text` | `str` | Redacted report |
| `changed` | `bool` | Whether content was modified |
| `output_path` | `Path` | Output destination |

### T7 — Longest stable event sequence

| Variable | Type | Purpose |
|---|---|---|
| `window_start` | `int` | Sliding-window start |
| `last_seen` | `dict[str, int]` | Last occurrence by event |
| `position` | `int` | Current event position |
| `best_start` | `int` | Start of best sequence |
| `best_length` | `int` | Length of best sequence |
| `sequence` | `list[str]` | Event sequence |

Update the best sequence only when `current_length > best_length`, retaining the first tie.

### T8 — Weather risk

| Variable | Type | Purpose |
|---|---|---|
| `forecast_key` | `tuple[str, str]` | Forecast lookup key |
| `forecast` | `dict` | Forecast record |
| `wind_kmh`, `precipitation_mm`, `wave_height_m` | `float` | Weather measurements; units retained in names |
| `recommendations` | `list[str]` | Risk recommendations |
| `upcoming_calls` | `list[dict]` | Upcoming port calls |

### T9 — Incident search

| Variable | Type | Purpose |
|---|---|---|
| `index` | `dict[str, list[str]]` | Search index; serialized index uses lists, never sets |
| `titles` | `dict[str, str]` | Incident title lookup |
| `query` | `str` | Search text |
| `query_words` | `set[str]` | Distinct query terms |
| `scores` | `dict[str, int]` | Match scores |
| `matches` | `list[tuple[str, int]]` | Ranked results |
| `cache_path` | `Path` | Cache file |
| `source_mtime`, `cache_mtime` | Numeric timestamps | Freshness comparison |

## 4. Documentation conventions and review

- Do not reuse `date` to mean both an ISO date string and a parsed `date` object without clarity.
- The T0–T4 and T6–T9 variable names and types above reproduce the teammate's planning reference; they are **not yet audited against the final code**.
- For T5, the additional locals, diagnostic tuple shapes, and result contracts reflect the actual shared functions rather than the original proposals.
- The team should agree on the permanent location of this document (`docs/VARIABLE-DICTIONARY.md`) and update it as functions are integrated.
- The original source was a planning/teaching pack, **not the finished submission**.
