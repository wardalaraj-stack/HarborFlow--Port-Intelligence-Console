HARBORFLOW PORT INTELLIGENCE CONSOLE - TEAM README

Run instructions
----------------
Command: python code/main.py
Python version tested: To be confirmed by the team.

Run automated tests: python -m pytest -q

The application should be started from the repository root directory.

Team members and concrete contributions
---------------------------------------
Name: Mado Sallom
Contribution:
- Task 4: Implemented the customer operations profile, including shipment counts, total weight, express shipment counts, unique destinations, and CSV export/update.
- Task 8: Implemented weather risk assessment for upcoming vessel calls, including date validation, forecast matching, and safety recommendations.
- Task 9: Implemented incident report search with a cached search index on a separate development branch. Integration is pending.
- Added automated acceptance, business-logic, and edge-case tests for Tasks 4 and 8, as well as tests for Task 9.

Name:
Contribution:

Name:
Contribution:

Name:
Contribution:

Architecture
------------
main.py responsibilities:
- Display the console menu.
- Read user input.
- Call the appropriate service functions.
- Display results and error messages.

data_access.py responsibilities:
- Define dataset and export paths.
- Load JSON and CSV files.
- Validate required fields and columns.
- Save generated output files.

operations.py responsibilities:
- Implement business logic and calculations.
- Build customer profiles.
- Select upcoming port calls.
- Match weather forecasts and generate recommendations.

text_tools.py responsibilities:
- Provide reusable text-processing functions.
- Support incident search text normalization in the Task 9 implementation.

File and error-handling design
------------------------------
How paths are resolved:
- Dataset and export paths are relative to the repository root.
- Run the program from the repository root using python code/main.py.

How malformed or missing input is handled:
- JSON collection loaders skip malformed files, invalid record structures, missing required fields, and duplicate IDs.
- CSV loaders validate required columns and skip rows with empty required values.
- Individual services handle additional validation and errors where applicable.

How generated files are updated safely:
- Task 4 writes customer profiles to exports/customer-profiles.csv.
- Existing customer profiles are updated rather than duplicated.
- A temporary file is written before replacing the original customer profile CSV.

Known limitations
-----------------
- This documentation describes the current development state, not the final integrated team application.
- Task 9 is implemented in a separate pull request and has not yet been integrated.
- Some services remain placeholders on the current development branch.
- Task 8 collects certain invalid-row diagnostics internally but does not display all of them in the console.
- Final team integration and end-to-end verification are still pending.