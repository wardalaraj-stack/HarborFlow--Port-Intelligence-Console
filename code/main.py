"""HarborFlow Port Intelligence Console - entry point.

This file only handles the menu and decides which service to run.
File loading lives in data_access.py, business rules in operations.py,
and text processing in text_tools.py.
"""

# ---------------------------------------------------------------------------
# Imports
# Project modules this file uses. Add new imports here, not further down.
# ---------------------------------------------------------------------------
import data_access

# The menu text is stored once as a constant so it is printed exactly the
# same way every time. Prompts and wording are part of the client contract,
# so do not change spacing, capitalization or punctuation here.
MENU_TEXT = """HARBORFLOW PORT INTELLIGENCE
1. List registered vessels
2. Inspect a vessel manifest
3. Identify priority cargo
4. Export a customer operations profile
5. Find port calls by month
6. Sanitize an incident report
7. Analyze the longest stable event sequence
8. Assess weather risk for upcoming calls
9. Search incident reports
10. Close console"""

MENU_ERROR = "Error - Select a service from 1 to 10."
CLOSE_MESSAGE = "Console closed. HarborFlow operational data remains safe."


# ---------------------------------------------------------------------------
# Service placeholders (Tasks 1-9)
# Each teammate replaces the body of their function with the real service.
# Keep the function names so the menu below keeps working.
# ---------------------------------------------------------------------------

def run_list_vessels():
    """Task 1: List registered vessels."""
    print("Service 1 not implemented yet.")  # TODO: replace


def run_inspect_manifest():
    """Task 2: Inspect a vessel manifest."""
    print("Service 2 not implemented yet.")  # TODO: replace


def run_priority_cargo():
    """Task 3: Identify priority cargo."""
    print("Service 3 not implemented yet.")  # TODO: replace


def run_export_customer_profile():
    """Task 4: Export a customer operations profile."""
    print("Service 4 not implemented yet.")  # TODO: replace


def run_port_calls_by_month():
    """Task 5: Find port calls by month."""
    print("Service 5 not implemented yet.")  # TODO: replace


def run_sanitize_incident():
    """Task 6: Sanitize an incident report."""
    print("Service 6 not implemented yet.")  # TODO: replace


def run_stable_sequence():
    """Task 7: Analyze the longest stable event sequence."""
    print("Service 7 not implemented yet.")  # TODO: replace


def run_weather_risk():
    """Task 8: Assess weather risk for upcoming calls."""
    print("Service 8 not implemented yet.")  # TODO: replace


def run_search_incidents():
    """Task 9: Search incident reports."""
    print("Service 9 not implemented yet.")  # TODO: replace


# ---------------------------------------------------------------------------
# Menu input
# ---------------------------------------------------------------------------

def read_menu_choice():
    """Ask for a menu number and return it as an int from 1 to 10.

    Returns None if the input is not a whole number or is out of range,
    so the caller can print the error and show the menu again.
    """
    raw = input("Select service: ")
    try:
        choice = int(raw)  # int() raises ValueError for text like "abc" or "2.5"
    except ValueError:
        return None
    if choice < 1 or choice > 10:
        return None
    return choice


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    """Run the console until the user selects option 10."""
    # Loop-state variable: the spec forbids break and exit(), so the loop
    # stops only when this flag is set to False (by option 10).
    running = True

    while running:
        print(MENU_TEXT)
        choice = read_menu_choice()

        if choice is None:
            print(MENU_ERROR)
        elif choice == 1:
            run_list_vessels()
        elif choice == 2:
            run_inspect_manifest()
        elif choice == 3:
            run_priority_cargo()
        elif choice == 4:
            run_export_customer_profile()
        elif choice == 5:
            run_port_calls_by_month()
        elif choice == 6:
            run_sanitize_incident()
        elif choice == 7:
            run_stable_sequence()
        elif choice == 8:
            run_weather_risk()
        elif choice == 9:
            run_search_incidents()
        else:
            # Only 10 can reach this branch, because read_menu_choice
            # already rejected everything outside 1-10.
            print(CLOSE_MESSAGE)
            running = False


# Only start the console when this file is run directly (python main.py),
# not when another module imports it.
if __name__ == "__main__":
    main()
