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
