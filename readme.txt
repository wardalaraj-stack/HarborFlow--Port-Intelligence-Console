HARBORFLOW PORT INTELLIGENCE CONSOLE - TEAM README

Run instructions
----------------
Command:
Python version tested:

Team members and concrete contributions
---------------------------------------

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

Architecture:

- `code/main.py`: User interaction, port-call selection, error handling, and formatted output.
- `code/data_access.py`: Existing port-call and manifest loaders.
- `code/operations.py`: Existing manifest lookup and identifier consistency check.
- `code/text_tools.py`: Longest stable-sequence algorithm.

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
Name:
Contribution:
---------------------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------------------
Name (if applicable):
Contribution:
---------------------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------------------
Architecture
------------
main.py responsibilities:
data_access.py responsibilities:
operations.py responsibilities:
text_tools.py responsibilities:

File and error-handling design
------------------------------
How paths are resolved:
How malformed or missing input is handled:
How generated files are updated safely:

Known limitations
-----------------
Write "None known" or describe each known limitation.
