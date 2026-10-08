# HarborFlow integrated implementation contract

This plan is the shared, recommended project contract for Tasks 1-9. It
reconciles the task plans; it is not application code. Assignment-mandated
behavior and exact strings remain authoritative. Decisions labeled
**Project policy** are integration choices where the assignment is silent,
not new assignment requirements. A task-specific plan may add detail but
must not contradict this contract.

## 1. Paths and data access

**Project policy:** derive `PROJECT_ROOT` from `Path(__file__).resolve().parent`
in `main.py`. Construct `dataset/`, `exports/`, and Task 9's
`dataset/incident-index.json` beneath that root, then pass the resulting paths
to loaders and writers. Do not resolve product paths against the process
working directory, hard-code a student's absolute path, or write other
persistent outputs outside `exports/`. Task 9's cache is the explicit
assignment exception to dataset read-only behavior.

Use one generic `load_json(path)` for a single JSON document. It reads one
UTF-8 document, requires a JSON object, and propagates parse, read, and
object-shape errors to its caller. It does not silently return an empty
object or handle directory-level recovery.

Use a common `LoadResult[T]` shape with `records: list[T]` and
`diagnostics: list[Diagnostic]`. A diagnostic carries a source path or CSV
row number, stable reason code, and relevant source value. Shared entry
points are `load_vessels(directory)`, `load_manifests(directory)`,
`load_shipments(directory)`, `load_incidents(directory)`,
`load_port_calls(path)`, and `load_weather(path)`; each returns this result
shape. Operations select matching business IDs from `.records` and retain
the diagnostics for task-appropriate reporting. Do not make repeated
per-identifier directory scans or discard loader diagnostics.

Directory JSON loaders enumerate matching files in sorted path order and
return a shared result containing `records` and structured `diagnostics`.
Each diagnostic identifies the source path and a stable error code/reason.
Malformed JSON and an individually invalid record (including a required
field/type violation) are recoverable: record a diagnostic, skip only that
file, and continue. Directory discovery failures and file I/O failures
propagate explicitly. Callers may report diagnostics using their own
assignment-appropriate output; they must not hide them or let one malformed
record suppress valid records.

CSV loaders validate the required header/schema and propagate directory,
file, decoding, and `csv.Error` failures explicitly. An incompatible header
is a schema error, not an empty result. For a structurally readable row,
preserve CSV source strings, especially `port_calls.csv.arrival_date`;
include source-row context for deterministic diagnostics. Per-row malformed
data can be reported and skipped where the consuming task requires it.
Duplicate `call_id` rows use the first row in CSV source order; diagnose and
ignore later rows with that ID.
Convert weather numeric fields in a focused per-row conversion block, not in
a generic loader that would lose source values or stop later rows. Require
finite converted values; `NaN` and infinities are malformed forecast data.

Shared record shapes:

- Vessel: non-empty string `vessel_id`, `name`, and `imo`, plus
  `capacity_teu`.
  **Project policy:** `capacity_teu` must be a non-negative JSON integer
  (booleans and numeric strings are not integers); zero is permitted.
  Invalid vessel files become loader diagnostics and are skipped. Task 1
  reports the number of rejected vessel files/records using its exact
  `Skipped vessel files: {count}` line.
- Port call: string `call_id`, `vessel_id`, `port_code`, and the unparsed
  source string `arrival_date`, plus source-row context for diagnostics.
  Date parsing requires exact `YYYY-MM-DD` syntax and a real calendar date,
  belongs to each operation, and must not invalidate the CSV or later calls.
- Manifest: string `call_id` and `vessel_id`, `shipment_ids` (ordered list
  of strings), and `event_codes` (chronological list of strings). Preserve
  both lists' order. Empty lists are valid. A matching manifest with
  invalid required fields is unusable and produces a diagnostic.
- Shipment: string `shipment_id`, `customer`, `destination`, and
  `priority`, with numeric `weight_kg` (not a boolean); optional boolean
  `hazardous` and `temperature_controlled` default to `false` when absent
  or null, and optional string `cargo_type` displays as `NOT PROVIDED`
  when absent or null. A present optional value of the wrong type
  invalidates that record. An unresolved or
  unusable shipment reference is task-specific:
  Task 2 prints/counts `MISSING RECORD`; Task 3 skips it without a cargo line
  or category count.
- Incident: required string fields `incident_id`, `call_id`, `title`, and
  `report`. Raw reports remain the source for both sanitization and search;
  Task 6 output never replaces Task 9 input.
- Weather row: string `port_code`, `date`, `wind_kmh`, `precipitation_mm`,
  and `wave_height_m` as read from CSV. Task 8 converts all three numeric
  source strings in its focused per-row conversion block.

One directory loader serves each JSON record type. Callers select by the
business identifier inside each parsed record, never by assuming a filename
is an identifier. Reuse the shared port-call records and vessel records
across Tasks 2, 3, 5, 7, and 8 as applicable. Data-access errors must remain
distinguishable from a valid empty collection or an unknown business ID.
If duplicate vessel or shipment identifiers occur, the first valid record
in sorted source-path order wins; diagnose and ignore later duplicates.

## 2. Calls, manifests, and linked-record recovery

**Project policy:** Task 2 selects a vessel's earliest valid call on or after
the valid reference date; equal dates use ascending `call_id`. Task 5 and
Task 8 retain their distinct assignment sort keys, specified below. Task 3
and Task 7 trim the entered call ID and compare case-insensitively to
`port_calls.csv`; an unknown ID prints the Task 3 exact string
`Port call not found.`. They load the manifest by matching its internal
`call_id` to the resolved call, not from its filename.

For duplicate matching call IDs in port_calls.csv, the first row in CSV
source order is selected and later duplicates are diagnosed/ignored. For
duplicate matching manifest IDs, use the first valid record in sorted
source-path order and diagnose/ignore later valid duplicates. A usable
manifest must have the matching `call_id`, the same `vessel_id` as the
selected call, `shipment_ids` as a list of strings, and `event_codes` as a
list of strings. A matching manifest that fails any of those checks is
diagnosed and skipped; if no usable matching manifest remains, use the
task-specific/shared unavailable-manifest behavior below. These policies
ensure Task 3 and Task 7 select the same call and manifest.

For all tasks, a manifest lookup considers matching records in sorted source
path order, uses the first valid matching manifest, and keeps diagnostics
from invalid files; later duplicate valid manifests are diagnosed and
ignored. If no usable matching manifest exists, Task 2 and Task 3
print their mandated `Manifest unavailable.` message; Task 7 uses the same
shared recovery message as a project consistency policy (not a Task 7
assignment string). Task 2 preserves manifest shipment order and prints a
missing record marker for every unresolved shipment reference. Task 3
preserves that order among resolved shipments and omits unresolved shipment
references from lines and totals. Task 7 passes the selected manifest's
event-code list unchanged to its sequence operation.

**Task 2 project policy:** the manifest line displays shipment ID, customer,
weight, and cargo type only, matching the demonstrated line shape.
`hazardous` and `temperature_controlled` remain available in the shared
shipment record for Task 3 classification but are not added to Task 2's
printed line.

## 3. Diagnostic and ordering conventions

**Project policy:** diagnostics are stable structured data, not ad hoc
loader prints. Include source path or CSV row number, a stable reason code,
and relevant source value. An operation decides which diagnostics its
assignment requires to be visible and renders them consistently; recoverable
row/file diagnostics never stop later valid records. Where the assignment
does not define text, use a concise deterministic `Skipped <source>
<location>: <reason>.` form. Report one primary failure per record in
validation order, rather than cascading messages for later checks of a row
already rejected. Sort source file discovery so repeated runs have the same
diagnostic order.

- Task 5 parses and validates `arrival_date` before vessel lookup; invalid
  date is the first diagnostic for that row. After a valid date, an unknown
  `vessel_id` is reported and skipped.
- Task 8 reports/skips invalid call dates and malformed weather rows while
  continuing later calls. Its exact mandated missing-forecast line remains
  `Forecast unavailable`.
- Task 1 counts recoverably invalid vessel files and records, without
  suppressing valid vessels.
- Fatal directory/CSV/schema/I/O failures are propagated to an explicit
  service-level error path. Do not convert them to empty collections,
  unknown-ID outcomes, or successful-looking reports.

## 4. Task-specific resolved policies

These are recommended project policies unless a bullet restates a literal
assignment rule. Do not replace or reword any exact assignment output
strings in the task plans.

### Task 4: profile output

Write the complete CSV to a uniquely named temporary file in the destination
directory, close it successfully, then atomically replace
`exports/customer-profiles.csv` with `os.replace`. On failure, surface the
write error and leave the prior destination intact; clean up only the
specific temporary file created by that write. Retain the in-memory
read/merge/write design, header order, exact header, two-decimal weight,
sorted unique destinations, and no-I/O path for an unmatched customer.

The PDF and dictionary do not define `express_count`. **Assumption supported
by the worked example, not a PDF mandate:** count records whose
`priority == "EXPRESS"`. The eight supplied Norra MedTech AB records yield
the demonstrated count of 3 under this rule.

### Task 3: classification reason

For the single EXPEDITE rule (`priority == "EXPRESS"` or `weight_kg >= 5000`),
use the demonstrated reason `express service` for either trigger. The PDF
defines one category rule and demonstrates this reason for EXPRESS
shipments; its use for a weight-only trigger is a project assumption, not a
separate assignment-mandated phrase.

### Task 5: month report

For every row, parse the full arrival date first. Report the first failure
only (invalid date before unknown vessel), skip that row, and continue.
Sort accepted calls by parsed date ascending, vessel name `casefold()`
ascending, and `call_id` ascending as the final deterministic tiebreaker.
Accept integer input after surrounding whitespace is stripped; reject
non-integer values and integers outside 1-12 with the mandated exact error
and repeat only the month prompt. The required display sort remains date
then vessel name; `call_id` only resolves otherwise equal keys.

### Task 6: identifier sanitization

Use whole-token matches: container and seal boundaries are Unicode
alphanumeric-or-underscore token boundaries (`\w` semantics) around exactly
four ASCII letters plus seven ASCII digits, or case-insensitive `SEAL-`
plus exactly six ASCII digits. Neither pattern may replace a valid-looking
substring embedded in a larger identifier token.

Email local characters are exactly ASCII letters/digits and `._%+-` before
`@`; domain characters are ASCII letters/digits, `.` and `-`, followed by a
final dot and at least two ASCII letters. Require the candidate to occupy a
whole token. On the left, reject an adjacent Unicode word character or any
of `._%+-@`. On the right, reject an adjacent Unicode word character or any
of `_%+-@`; a period is domain continuation (and rejects the candidate)
when followed by a Unicode word character, hyphen, or another
email-allowed punctuation character. Preserve a terminal sentence period
only when the next character is absent or is punctuation/whitespace rather
than a possible token continuation. This prevents partial email matches
inside larger tokens while retaining sentence punctuation. Apply `re.sub()`
in this order: email, container, seal. This
protects an email containing an identifier-shaped substring from an earlier
ID substitution. Determine `changed` by comparing final text to original.
Preserve every character outside replaced spans.

Focused boundary fixtures must include valid tokens at punctuation/space/
line boundaries, mixed-case container and `SEAL-` prefixes, one-character-
longer container and seal strings, identifier strings embedded beside
letters/digits/underscores, valid email at sentence end, email candidates
adjacent to local/domain continuation characters on both sides, a period
followed by a domain/token continuation versus a terminal sentence period,
a valid-looking address embedded in a larger token, and email spans
containing container/seal-like text. A no-change result
must neither write nor delete the target file, even if a previous output
exists.

### Task 7: event sequence

Use Task 3's shared trimmed/case-insensitive call-ID resolution and manifest
loader. Validate `event_codes` as a list of strings before sequence
analysis; an unusable manifest follows the shared unavailable-manifest
path. Preserve source order and the strict-greater-than winner update, so
the first maximum-length window wins. For an empty valid list, print
`Longest stable sequence length: 0` and a `Sequence: ` line with nothing
after the space. That empty-list display is a project policy; the two
non-empty output shapes in the assignment remain exact.

### Task 8: weather report

Validate each source call date, then keep valid selected-vessel calls on or
after the reference date. Sort by arrival date and then `call_id` ascending.
Convert all three weather fields (`wind_kmh`, `precipitation_mm`,
`wave_height_m`) inside one focused per-row try block and require finite
numeric values; on conversion or finiteness failure, diagnose and skip only
that forecast row. For duplicate valid
`(port_code, date)` keys, the first valid row in CSV source order wins;
report each later duplicate and do not overwrite the first.

Print each qualifying call as its own report block in sorted order, with one
blank line between blocks and no added heading. Keep the demonstrated
three-line block and exact recommendation strings; render all three
numeric values to one decimal place, matching the PDF example. Apply warning
recommendations independently in table order; print the normal plan only
when all warning conditions are false. A malformed matching forecast row
is diagnosed; if no valid forecast remains for the call, also print the
mandated `Forecast unavailable` line for that call. If no valid upcoming
calls remain, print exactly `No upcoming port calls found.` after any
required source-row diagnostics.

Require a real ISO calendar date for each weather row; an invalid date or
numeric field makes that weather row invalid and recoverably diagnosed.
Use the shared non-zero-padded `D Month YYYY` display date for Tasks 2 and 8;
Task 5 retains its assignment-demonstrated zero-padded `DD Month YYYY`
format.

### Task 9: tokenizer and cache

Use exactly the same tokenizer on reports and queries:
`re.findall(r"[^\W_]+", text.casefold(), flags=re.UNICODE)`. Thus Unicode
letters/digits form tokens; punctuation, hyphens, apostrophes, and
underscores delimit tokens. Distinct query words score once. If a query
normalizes to no tokens, print `Search query contains no searchable words.`
and do not score. For a non-empty query with no positive matches, print the
normal required `Matches for '{query}':` heading and then
`No matching incidents found.`; never print zero-score rows. These two
messages are project policies, not PDF-mandated strings.

Rebuild serialization is deterministic: exactly the top-level keys `index`
and `titles`; sorted word keys and title keys; sorted, de-duplicated ID
lists. For every cache decision, first successfully discover a non-empty
sorted list of incident JSON source paths and stat every source file.
Discovery or stat errors are fatal and explicit; an empty source-file list is
an explicit source-data error, not a reusable cache. Cache reuse validation
then checks only the exact top-level object keys, required value types, and
freshness against all discovered source mtimes. If an existing cache has that
valid schema and is fresh, reuse it without parsing or reading incident JSON
contents, even when those files would currently fail JSON or incident-schema
validation. Sparse but otherwise valid cache contents are reusable; if a
positive posting has no corresponding cached title, render its match with an
empty title field rather than rereading source records or rejecting the
cache. Do not reject a cache for unsorted entries, missing cross-map IDs, or
other extra consistency rules not required by the assignment. Equal
cache/source modification times are fresh because the cache is not older.
Missing, malformed, wrong-schema, or stale cache data triggers a rebuild.
Other cache read I/O and permission errors propagate explicitly; do not turn
an inaccessible cache into an ordinary cache miss.

When rebuilding, load the discovered source records. Individual malformed
incident files may be skipped with diagnostics when at least one valid
incident record remains. If no valid source incident records remain, surface
an explicit source-loading failure and leave any existing cache untouched; do
not create or report a successful empty index. For duplicate incident IDs,
the first valid record in sorted path order wins and each later duplicate is
diagnosed and skipped.

Write cache JSON via a uniquely named temporary file in `dataset/`, close
the complete UTF-8 document, then `os.replace` the cache path. A write or
replace failure propagates explicitly; it must not be reported as a
successful rebuild. The cache remains the sole read-only-dataset exception.

## 5. Plan integration and status

TASK-1 through TASK-9 plans cross-reference this document. Their earlier
draft interface alternatives and unresolved-policy questions are superseded
only where they conflict with the shared contract or the task addenda. All
other task-specific requirements, exact output strings, and acceptance
cases remain in force.

Review gates mentioned in earlier drafts are optional internal
planning/review workflow only; they are not assignment or user requirements
and do not block implementation by themselves. Concrete unresolved
implementation issues must still be stated and resolved. This plan
revision did not run project commands, tests, builds, or reviewer
approvals. The existing
test-ledger.csv is intentionally unchanged; this plan does not claim any
test or acceptance status for it.
