# Task 2 Loader Checkpoint Report

## Scope

Implemented the shared record-loading layer in `code/data_access.py` only.
The implementation does not move files, add menu/service behavior, or modify
any dataset file.

## Changes

- Added shared `Diagnostic` and `LoadResult` dataclasses.
- Added UTF-8 object-only `load_json`.
- Added deterministic, case-insensitive JSON directory enumeration.
- Added vessel, manifest, and shipment validation, including optional-field
  handling and boolean-safe numeric validation.
- Added recoverable malformed-file, invalid-record, and duplicate-identifier
  diagnostics while retaining the first valid record.
- Added schema-checked CSV loading for port calls with `newline=""`, preserved
  source strings, row diagnostics, and first-row duplicate handling.

## Commit

- Commit: `6177bcd7057af6e6664451ad3ad8af59eb98201c`
- Message: `feat: add Task 2 record loaders`

## Tests and output

Focused command:

```text
python -m unittest discover -s tests -p "test_task_2.py" -v
```

Result:

```text
Ran 12 tests in 0.007s
FAILED (errors=15)
```

The failures are expected at this checkpoint because the existing focused
file also contains later Task 2 operation/service tests, while
`code/operations.py` and `code/main.py` remain intentionally unimplemented.
The loader smoke test against the shipped dataset completed successfully:
three vessels plus one malformed-vessel diagnostic, six port-call rows,
five manifests, and ten shipments were loaded.

## Self-review

- `load_json` propagates file and JSON parsing errors and raises the exact
  required message for non-object top-level values.
- JSON files are sorted by case-folded filename and only the first valid
  business identifier is retained.
- Validation rejects missing/empty required text, invalid list contents,
  invalid vessel capacity, boolean shipment weights, and wrong optional
  field types; absent and null optional values remain valid.
- Port-call dates remain unparsed strings so later operations can skip
  invalid calendar dates without discarding subsequent rows.
- `git diff --check` passed.
- No protected dataset or unrelated working-tree files were changed.

## Concerns

The focused test file currently has no direct loader assertions; hidden or
later tests will exercise the structured diagnostic fields. Diagnostic codes
are stable, concise loader-level codes (`malformed_json`, `invalid_record`,
`duplicate_identifier`, and `invalid_row`) and can be rendered by later
services without coupling those services to loader text.

## Review Fixes

Added `tests/test_data_access_task_2.py` with focused coverage for:

- malformed JSON recovery and continuation to later files;
- required-field and type validation for vessels, manifests, and shipments;
- case-folded filename ordering;
- retaining the first exact duplicate business ID while accepting a
  case-variant ID as distinct;
- CSV required-header failures and invalid/duplicate row diagnostics; and
- source paths, row locations, and unparsed date strings.

The loader duplicate policy is exact business-ID equality. No repository
contract requires case-insensitive identifier identity; case-insensitive
matching remains an operation-layer concern where applicable.

Changed JSON and CSV duplicate checks in `code/data_access.py` from
case-folded keys to exact keys.

## Fix Test Output

Loader-focused command:

```text
python -m unittest discover -s tests -p "test_data_access_task_2.py" -v
```

```text
Ran 4 tests in 0.036s
OK
```

Existing Task 2 command:

```text
python -m unittest discover -s tests -p "test_task_2.py" -v
```

```text
Ran 12 tests in 0.009s
FAILED (errors=15)
```

Those remaining failures are the previously expected operation/service
failures because later Task 2 behavior is not implemented in
`code/operations.py` and `code/main.py`.

## Fix Commit

- Commit: `2f4823c1fd20845e34c45b0fb79093517b1f410d`
- Message: `fix: tighten Task 2 loader diagnostics`
