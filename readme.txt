HARBORFLOW PORT INTELLIGENCE CONSOLE - TEAM README

Run instructions
----------------
Command:
Python version tested:

Team members and concrete contributions
---------------------------------------
Name: Abdalsalam Ward Alaraj
Contribution:
- Served as the technical lead by coordinating the integration of the separate task 
implementations into the main application.
- Designed the overall structure and organized the project into task-specific implementation and review files.
- Created the detailed task instruction files describing the required inputs, 
calculations, outputs, validation rules, testing checklists, and acceptance criteria.
- Maintained project files, structure, and documentation.
- Created learning resources and documentation to support team members' understanding of the project and its components.
- Created simplified guides and explanations to help team members quickly understand complex parts of the project.
- Created the allowed-tools and limitations guide to keep the solution within the 
assignment's permitted Python scope.
- Independently implemented Task 2 
- Independently implemented Task 6 
- Hosted and managed the project repository, including branch coordination, merging 
team changes, and maintaining the shared project state.
- Stress-tested the application and checked normal, boundary, and invalid-input 
cases across the required tasks.
- Reviewed the implementation against the allowed-tools and limitations guide, 
including restrictions on dictionaries, files, regular expressions, sets, 
list comprehensions, classes, third-party packages, and exit().
- Validated the work submitted by group members and integrated the completed 
task implementations into the final console structure.

--------------------------------------------------------------------------------------------------------------------
Name: Raydel Savón

Contribution: Task 5 - Find Port Calls by Month

Implemented and tested the monthly port-call reporting service, including:

- Month input validation (1–12), with repeated prompts for invalid inputs.
- Loading port-call records and resolving vessel names through vessel IDs.
- Validating arrival dates and handling unknown vessels.
- Filtering port calls by selected month across different years.
- Sorting results by arrival date, vessel name (case-insensitive), and call ID.
- Formatting reports with vessel names, arrival dates, port codes, and call IDs.
- Displaying "No port calls found." when no valid matching records exist.
- Handling missing files, malformed JSON, missing required CSV columns, and CSV parsing errors without crashing the application.
- Returning control to the main menu after service execution or recoverable errors.

Testing and quality assurance:

Executed and verified acceptance tests and additional edge cases, including:

- November report sorting and formatting.
- Unknown vessel with no valid matching calls.
- Invalid arrival date combined with unknown vessel ID.
- Month input containing surrounding spaces, a leading plus sign (+10), and a leading zero (010).
- Case-insensitive alphabetical sorting for identical dates.
- Call-ID tie-breaking when arrival dates and vessel names are identical.
- Missing vessel directory.
- CSV file missing the required arrival_date column.
- Simulated CSV parsing failure.
- Main-menu recovery after a simulated CSV error.

Test results were documented in test-ledger.csv. Temporary simulations were performed without modifying the supplied dataset.

Documentation:

- Reviewed the team's existing Data and Variable Dictionary document.
- Prepared docs/VARIABLE-DICTIONARY.md, consolidating the original variable reference for Tasks 0–9 with the actual variables and data structures used in Task 5.
- Preserved the distinction between the existing dataset/DATA-DICTIONARY.md and the new variable dictionary.
- Documented the Task 5 processing flow: input validation, data loading, record validation, month filtering, sorting, and formatted output.

Status: Task 5 functionality and the listed acceptance and edge-case tests have passed. Final team review, repository integration, and submission checks is also done.



Contribution: Task 7 - Longest Stable Event Sequence
----------------------------------------------------

Implemented and tested the stable event-sequence analysis service, including:

- Accepting a Call ID with case-insensitive matching and whitespace normalization.
- Retrieving the selected port call and its matching manifest.
- Verifying consistency between the manifest's Call ID and vessel ID.
- Validating event codes before processing.
- Applying a sliding-window algorithm to find the longest contiguous sequence without repeated event codes.
- Preserving the earliest sequence when multiple sequences have the same maximum length.
- Returning the sequence length and its event codes in chronological order.
- Handling unknown Call IDs, unavailable manifests, and selected data-loading errors without terminating the console.

Testing and quality assurance:

Verified function-level tests covering repeated events, the official assignment example, equal-length sequences, empty input, single-event input, identical events, unique events, and previous occurrences outside the current window.

Verified integration and console tests covering manifest retrieval, successful port-call analysis, unknown Call IDs, unavailable manifests, input normalization, and menu recovery.

Simulated `FileNotFoundError` exceptions for the port-call and manifest loaders without modifying the dataset. Results were recorded in `test-ledger.csv`.

**Status: Task 7 implementation and the listed tests have passed. Final documentation review, team integration, and submission checks are also done.

---------------------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------------------

Name: Waldean Nelson

Contribution: Task 0 - Product Shell

- Built the main menu loop in main.py using a loop-state variable (no exit() or break).
- Rejected non-integer and out-of-range input with "Error - Select a service from 1 to 10."
- Connected all services to the menu so each returns to the menu when finished.
- Caught FileNotFoundError, json.JSONDecodeError, csv.Error and ValueError where a useful message can be given, with no blanket except.
- Closed the console only through option 10 with "Console closed. HarborFlow operational data remains safe."

Contribution: Task 1 - List Registered Vessels

- Wrote load_json(path) for single files and load_vessels(directory) for the vessel folder.
- Checked that vessel_id, name, imo and capacity_teu exist in each record.
- Skipped and counted malformed or incomplete files without hiding valid vessels.
- Sorted vessels by name (case-insensitive) and formatted capacity with thousands separators.

Contribution: Task 3 - Identify Priority Cargo

- Matched call IDs case-insensitively after removing surrounding spaces.
- Wrote a pure classification function that returns category and reason, with rule order visible in the code.
- Printed each shipment in manifest order, followed by category totals.
- Handled unknown calls ("Port call not found") and missing or malformed manifests ("Manifest unavailable").

Testing:

- Menu: valid choices, text input, 0, 11 and empty input.
- Vessels: malformed JSON file, missing required field, mixed valid and invalid files.
- Classification: each rule alone, rule order when several conditions apply, missing boolean flags.
- Calls: known call ID, unknown call ID, missing manifest.
- Results were recorded in test-ledger.csv.
---------------------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------------------

Name: Mado Sallom
Contribution: Tasks 4, 8 and 9; integration and related tests.

Task 4 — Export a customer operations profile
- Integrated menu option 4 in main.py.
- Built the customer profile in operations.py by matching customer names case-insensitively and ignoring surrounding whitespace.
- Calculated shipment_count, total_weight_kg (two decimals), express_count and sorted unique destinations.
- Saved new or updated customer rows in exports/customer-profiles.csv through data_access.py, without duplicating customer rows.
- Wrote automated checks for profile aggregation, missing customers and CSV update behavior.

Task 8 — Assess weather risk for upcoming calls
- Integrated menu option 8 in main.py and supporting business logic in operations.py.
- Validated the reference date, selected upcoming vessel calls, ordered them chronologically and matched forecasts by port code and arrival date.
- Applied wind, wave and rain thresholds; returned multiple safety recommendations in the prescribed order when applicable.
- Handled missing forecasts without stopping later calls.
- Added tests covering boundary values, combined rules, invalid dates, missing forecasts, multiple calls, lookup matching and malformed numeric forecast rows.

Task 9 — Search incident reports
- Integrated menu option 9 with the shared console on main.
- Implemented normalized word tokenization in text_tools.py and an inverted incident index and title lookup in operations.py.
- Prevented repeated incident IDs within each word list by deduplicating report words.
- Implemented search scoring by distinct matching query words and ordering by descending score then incident ID.
- Used dataset/incident-index.json as a reusable cache. Added load, validate, stale-cache rejection and save logic in data_access.py.
- Added 14 automated Task 9 tests in tests/test_task_9.py and manually demonstrated searching for 'reefer delay' through menu option 9.
---------------------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------------------
Name (if applicable):
Contribution:
---------------------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------------------
Architecture - Abdaalsalam Alaraj
------------
HarborFlow is a standard-library, menu-driven Python console application.
It separates console interaction, data access, business rules, and text
processing so each responsibility can be understood and tested independently.

| Module | Responsibility |
| --- | --- |
| `main.py` | Starts the menu, obtains and validates user input, invokes services 1-9, presents reports, and displays recoverable errors. |
| `data_access.py` | Defines dataset and export paths; loads, validates, sorts, and writes JSON and CSV data; returns loader diagnostics instead of printing them. |
| `operations.py` | Holds business rules that do not print or read files directly, including manifest selection, cargo classification, month filtering, weather assessment, and incident indexing/search. |
| `text_tools.py` | Provides regular-expression incident sanitization, the stable event-sequence algorithm, and incident-search word normalization. |

Data and control flow
---------------------
1. The user selects a service in `main.py`.
2. The service requests records through `data_access.py`. JSON collections are
   returned as dictionaries keyed by their business identifiers, and CSV files
   are returned as rows in source order.
3. `data_access.py` returns both usable records and diagnostics for individual
   records it skipped. Services decide which diagnostics to show.
4. `main.py` sends valid records and normalized user input to `operations.py`
   or `text_tools.py`.
5. The service prints the resulting report or error message. Services that
   generate durable output write under `exports/`.

The dataset is intentionally relational: port calls reference vessels,
manifests reference port calls and shipments, and incidents reference port
calls. The application resolves these links using identifiers stored inside
records rather than filenames.


File and error-handling design
------------------------------
Path resolution
~~~~~~~~~~~~~~~
`data_access.py` builds all source and output paths from relative `Path`
values. Source records reside below `dataset/`; generated customer profiles
and sanitized incident reports reside below `exports/`. This keeps supplied
data separate from generated output.

JSON handling
~~~~~~~~~~~~~
`load_json_collection()` processes JSON files in deterministic filename order.
It keeps valid object records, keyed by their in-record business ID, and
returns diagnostics for malformed JSON, missing files encountered during
loading, non-object payloads, missing required fields, and duplicate IDs.
The first valid record for a duplicate ID is retained. Individual bad files do
not stop other valid records from loading.

CSV handling
~~~~~~~~~~~~
`load_csv_rows()` verifies required headers before processing rows. It keeps
complete rows as source strings and returns line-number diagnostics for rows
with absent or blank required cells. Missing CSV files, parsing failures, and
invalid headers are deliberately raised to the calling service, which can
present a service-specific message instead of continuing with incomplete
source data.

User input and service recovery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The console validates menu choices, dates, month numbers, and incident list
selections before processing a request. Invalid input is normally reported
with the required error text and only the relevant prompt is repeated.
Several services catch expected `FileNotFoundError`, `ValueError`, `csv.Error`,
or `OSError` exceptions, print a human-readable message, and return control to
the menu. The Task 9 incident-search cache is treated as expendable: a
missing, stale, malformed, or structurally invalid cache is ignored and
rebuilt from the source incident records.

Generated output
~~~~~~~~~~~~~~~~
Customer-profile updates create the output directory when necessary, write a
temporary CSV in that directory, then atomically replace the final profile
file. Sanitized incident reports create `exports/sanitized/` when needed and
write `<incident_id>-sanitized.txt`. The incident-search index is written as
formatted JSON at `dataset/incident-index.json`.


Known limitations
-----------------
The project intentionally keeps malformed and incomplete sample data so that
the console can demonstrate recovery behavior. The following are known
implementation limitations, not intentional data cases:

- **Repository-root working directory required.** All configured paths are
  relative. Running the program from another current working directory can
  make the dataset and exports unavailable.
- **Uneven top-level loader recovery.** Tasks 1, 3, and 6 call shared loaders
  without their own file/format exception handlers. A missing or unreadable
  source can therefore terminate those services rather than show a
  service-specific recovery message.
- **A missing JSON directory looks empty.** `load_json_collection()` uses
  `Path.glob()`, which returns no records when its directory does not exist;
  it does not itself report that absence. Task 5 adds an explicit vessel
  directory check, but other users of the loader do not.
- **Task 2 uses the wrong unavailable-manifest message.** When no compatible
  manifest is found, it prints `Port call not found.` instead of the specified
  `Manifest unavailable.` This outcome is recorded as a failure in
  `test-ledger.csv`.
- **Incident validation is incomplete.** `validate_incidents()` checks that
  every required field exists, but its empty/non-string check applies only to
  the last required field. It is also not currently used by the incident
  loader. An empty earlier incident field can therefore be accepted.
- **Task 3 assumes optional classification fields exist.** Its cargo
  classification indexes `hazardous` and `temperature_controlled` directly,
  even though the shared data model treats those fields as optional. A record
  without either field can raise `KeyError`.
- **Write robustness differs by output type.** Customer-profile saving uses an
  atomic replacement, but sanitized-report and incident-index writes are
  direct writes. An interruption while those files are being written can leave
  partial output.
- **Interactive interface only.** There are no command-line arguments,
  configuration options, logging, or API endpoints; the program is intended
  to be run through its numbered console menu.
- **Coverage is not yet uniform.** The committed automated tests focus on
  Tasks 2, 4, 8, and 9. Other tasks rely more heavily on recorded manual and
  ledger-based verification.
- **Task 9 has limited error feedback.** It performs several data transformations 
  and writes multiple outputs, but its error messages do not always indicate which specific step failed.
- **Task 8 does not validate input thoroughly.** It assumes that all required fields are 
  present and correctly formatted, which can lead to unexpected errors if the input data is incomplete or malformed.
- **