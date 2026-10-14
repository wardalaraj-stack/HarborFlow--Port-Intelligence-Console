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

Status:

Task 5 functionality and the listed acceptance and edge-case tests have passed. Final team review, repository integration, and submission checks remain pending.

**Contribution: Task 7 - Longest Stable Event Sequence**

Implemented and tested the stable event-sequence analysis service, including:

- Accepting a Call ID with case-insensitive matching and whitespace normalization.
- Retrieving the selected port call and its matching manifest.
- Verifying consistency between the manifest's Call ID and vessel ID.
- Validating event codes before processing.
- Applying a sliding-window algorithm to find the longest contiguous sequence without repeated event codes.
- Preserving the earliest sequence when multiple sequences have the same maximum length.
- Returning the sequence length and its event codes in chronological order.
- Handling unknown Call IDs, unavailable manifests, and selected data-loading errors without terminating the console.

**Testing and quality assurance:**

Verified function-level tests covering repeated events, the official assignment example, equal-length sequences, empty input, single-event input, identical events, unique events, and previous occurrences outside the current window.

Verified integration and console tests covering manifest retrieval, successful port-call analysis, unknown Call IDs, unavailable manifests, input normalization, and menu recovery.

Simulated `FileNotFoundError` exceptions for the port-call and manifest loaders without modifying the dataset. Results were recorded in `test-ledger.csv`.

**Architecture:**

- `code/main.py`: User interaction, port-call selection, error handling, and formatted output.
- `code/data_access.py`: Existing port-call and manifest loaders.
- `code/operations.py`: Existing manifest lookup and identifier consistency check.
- `code/text_tools.py`: Longest stable-sequence algorithm.

**Status:**

Task 7 implementation and the listed tests have passed. Final documentation review, team integration, and submission checks remain pending.
---------------------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------------------

Name:
Contribution:
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
