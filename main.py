"""HarborFlow Port Intelligence Console - entry point.

This file only handles the menu and decides which service to run.
File loading lives in data_access.py, business rules in operations.py,
and text processing in text_tools.py.
"""

# ---------------------------------------------------------------------------
# Imports
# Project modules this file uses. Add new imports here, not further down.
# ---------------------------------------------------------------------------
import csv

import data_access
import operations
import text_tools

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

# ---------------------------------------------------------------------------
# Task 1: List Registered Vessels
# ---------------------------------------------------------------------------

def print_vessel_list(dict_of_dict, skip_lst):
    """Print the registered vessel list from already-loaded data (used by Task 1 and Task 2)."""

    num_skipped_files = len(skip_lst)
    print("Registered HarborFlow vessels:")
    
    for vessel in sorted(dict_of_dict.values(), key=lambda vessel: vessel["name"].lower()):
        vessel_name = vessel["name"]
        imo_num = vessel["imo"]
        capacity = vessel["capacity_teu"]
        print(f"- {vessel_name} | IMO {imo_num} | {capacity:,} TEU")

    # print the number of skipped files       
    print(f"Skipped vessel files: {num_skipped_files}")


def run_list_vessels():
    """Task 1: List registered vessels."""
    # create variable that holds the tuple (dict, list)
    vessel_tup = data_access.load_vessels(directory=data_access.VESSELS_DIR)
    # unpack that tuple
    dict_of_dict, skip_lst = vessel_tup

    # hand the loaded data to the printing function
    print_vessel_list(dict_of_dict, skip_lst)

# def run_list_vessels():

#     """Task 1: List registered vessels."""
#     # create variable that holds the tuple (dict, list)
#     vessel_tup = data_access.load_vessels(directory=data_access.VESSELS_DIR)
#     # unpack that tuple
#     dict_of_dict, skip_lst = vessel_tup
#     num_skipped_files = len(skip_lst)

#     print("Registered HarborFlow vessels:")
#     # print the correct vessel info - in alphabectical/sorted order
#     #lambda is the Python keyword for making a small function without a name, written in one line.
#     #reads as: “a function that takes vessel and returns vessel["name"].lower()
#     for vessel in sorted(dict_of_dict.values(), key=lambda vessel: vessel["name"].lower()):
#         vessel_name = vessel["name"]
#         imo_num = vessel["imo"]
#         capacity = vessel["capacity_teu"]
#         print(f"- {vessel_name} | IMO {imo_num} | {capacity:,} TEU")

#     # print the number of skipped files       
#     print(f"Skipped vessel files: {num_skipped_files}")

# ---------------------------------------------------------------------------
# Task 2: START Inspect a vessel manifest
# ---------------------------------------------------------------------------

def run_inspect_manifest():
    try:
        vessels, vessel_problems = data_access.load_vessels()
        calls, _ = data_access.load_port_calls()
        manifests, _ = data_access.load_manifests()
        shipments, _ = data_access.load_shipments()
    except (FileNotFoundError, ValueError, csv.Error) as error:
        print(f"Error - {error}")
        return

    # reuse Task 1's printing with the data already loaded above (no second file read)
    print_vessel_list(vessels, vessel_problems)

    vessel_name = input("Vessel name: ")

# def run_inspect_manifest():
#     try:
#         vessels, vessel_problems = data_access.load_vessels()
#         calls, _ = data_access.load_port_calls()
#         manifests, _ = data_access.load_manifests()
#         shipments, _ = data_access.load_shipments()
#     except (FileNotFoundError, ValueError, csv.Error) as error:
#         print(f"Error - {error}")
#         return

#     print("Registered HarborFlow vessels:")
#     for vessel in vessels.values():
#         print("\n"
#             f"- {vessel['name']} | IMO {vessel['imo']} | "
#             f"{vessel['capacity_teu']:,} TEU"
#         )
#     for filename, reason in vessel_problems:
#         print("\n"
#             f"Skipped {filename}: {reason}")
#     print(f"Skipped vessel files: {len(vessel_problems)}\n")

#     vessel_name = input("Vessel name: ")
    vessel = operations.find_vessel_by_name(vessel_name, vessels)

    if vessel is None:
        print("Vessel not found.")
        return

    reference_date = ask_reference_date()
    call = operations.select_upcoming_call(
        calls,
        vessel["vessel_id"],
        reference_date,
    )

    if call is None:
        print("No upcoming port calls found.")
        return

    manifest = operations.find_manifest(manifests, call)
    if manifest is None:
        print("Manifest unavailable.")
        return

    report = operations.build_manifest_report(
        vessel,
        call,
        manifest,
        shipments,
    )
    print_manifest_report(report)


def ask_reference_date():
    """Ask until the user enters a real YYYY-MM-DD date."""
    while True:
        value = input("Reference date (YYYY-MM-DD): ")
        try:
            return operations.parse_reference_date(value)
        except ValueError:
            print("Error - Date must use YYYY-MM-DD.")


def print_manifest_report(report):
    """Print the Task 2 report in the required format."""
    print(
        "\n" #remove
        f"Manifest for {report['vessel_name']} | "
        f"Call {report['call_id']} | {report['date_display']}"
        "\n" #remove
    )

    for number, line in enumerate(report["lines"], start=1):
        if line["resolved"]:
            print(
                "\n" #remove
                f"{number}. {line['shipment_id']} | "
                f"{line['customer']} | {line['weight_kg']} kg | "
                f"{line['cargo_type']}"
            )
        else:
            print(f"{number}. {line['shipment_id']} | MISSING RECORD")

    print(f"""
Declared shipments: {report['declared']}
Resolved weight: {report['resolved_weight']:.2f} kg
Missing shipment records: {report['missing']}
""")

# ---------------------------------------------------------------------------
# Task 2: END
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
#task_03 starts here - Identify Priority Cargo
#-----------------------------------------------------------------------
def run_priority_cargo():

    manifest_tup = data_access.load_manifests(directory=data_access.MANIFESTS_DIR)
    #unpack that tuple
    call, skipped_manifests = manifest_tup

    shipment_tup = data_access.load_shipments(directory=data_access.SHIPMENTS_DIR)
    ship_ids, skipped_shipments = shipment_tup

    call_id = input("Enter call_id: ").strip().upper()

    if call_id in call:
        shipment_tracker, control_count, cc_count, exp_count, stan_count = operations.find_shipment_ids(call, call_id, ship_ids)
        for ship_id, category, reason in shipment_tracker:
            print(f"{ship_id} | {category} | {reason}")
        print(f"Category totals: CONTROLLED={control_count}, COLD CHAIN={cc_count}, EXPEDITE={exp_count}, STANDARD={stan_count}")
    else:
            print("Manifest unavailable")

# ---------------------------------------------------------------------------
#task_03 ends here - Identify Priority Cargo
#-----------------------------------------------------------------------

def run_export_customer_profile():
    """Task 4: Export a customer operations profile."""
    print("Service 4 not implemented yet.")  # TODO: replace


#--------------------------------------------------------------------------------------
# START Task 5  ------------------
#--------------------------------------------------------------------------------------

def run_port_calls_by_month():
    """Ask for a month and display its valid port calls in sorted order."""

    # Repeat only the month prompt until the input is valid.
    valid_month = False

    while not valid_month:
        month_text = input("Month (1-12): ")

        try:
            month = int(month_text)
        except ValueError:
            print("Error - Enter a month from 1 to 12.")
        else:
            if 1 <= month <= 12:
                valid_month = True
            else:
                print("Error - Enter a month from 1 to 12.")

    # Load source data and handle expected file or parsing failures.
    try:
        records, issues = data_access.load_port_calls()

        # The current vessel loader silently accepts a missing directory.
        # Check it here so missing source data is reported explicitly.
        if not data_access.VESSELS_DIR.is_dir():
            raise FileNotFoundError("Vessel directory not found.")

        vessel_by_id, vessel_issues = data_access.load_vessels()

    except FileNotFoundError as error:
        print("Port calls unavailable:", error)
    except csv.Error:
        print("Port calls unavailable: CSV could not be read.")
    except ValueError as error:
        print("Port calls unavailable:", error)
    else:
        # Loaders return diagnostics; this function displays them.
        for line_number, reason in issues:
            print(f"Skipped port_calls.csv line {line_number}: {reason}.")

        for source_file, reason in vessel_issues:
            print(f"Skipped vessel file {source_file}: {reason}.")

        # Validate, resolve vessels, filter by month and sort the calls.
        matching_calls, call_issues = operations.collect_month_calls(
            month, records, vessel_by_id
        )

        for call_id, reason in call_issues:
            print(f"Skipped port call {call_id}: {reason}.")

        if not matching_calls:
            print("No port calls found.")
        else:
            # Explicit English labels keep the report language consistent.
            month_names = (
                "January", "February", "March", "April",
                "May", "June", "July", "August",
                "September", "October", "November", "December"
            )

            # Tuple positions start at zero; month numbers start at one.
            month_name = month_names[month - 1]
            print(f"Port calls in {month_name}:")

            for record in matching_calls:
                call_date = record["call_date"]

                # Task 5 requires a two-digit day, such as 02.
                date_display = (
                    f"{call_date.day:02d} "
                    f"{month_names[call_date.month - 1]} "
                    f"{call_date.year:04d}"
                )

                print(
                    f"- {date_display} | {record['vessel_name']} | "
                    f"{record['port_code']} | {record['call_id']}"
                )

#--------------------------------------------------------------------------------------
# END of Task 5 ------------------
#--------------------------------------------------------------------------------------


def run_sanitize_incident():
    """Task 6: Sanitize an incident report."""
    incidents, _skipped = data_access.load_incidents()
    ordered = data_access.sort_incidents(incidents.values())

    if not ordered:
        print("No incident reports available.")
        return

    for number, incident in enumerate(ordered, start=1):
        print(f"{number}. {incident['title']}")

    while True:
        try:
            choice = int(input("Select incident: ").strip())
            if 1 <= choice <= len(ordered):
                break
        except ValueError:
            pass
        print("Error - Select a listed incident.")

    selected = ordered[choice - 1]
    sanitized, changed = text_tools.sanitize_text(selected["report"])

    if not changed:
        print("Incident contains no share-sensitive identifiers.\n")
        return

    data_access.write_sanitized_report(
        selected["incident_id"],
        sanitized,
        data_access.SANITIZED_DIR,
    )
    print(
        "Incident sanitized:"
        f"{selected['incident_id']}\n"
    )

#--------------------------------------------------------------------------------------
# START of Task 7 ------------------
#--------------------------------------------------------------------------------------

def run_stable_sequence():
    """Task 7: Find the longest contiguous event sequence without repetitions."""

    # Normalize the user's input to match stored Call IDs.
    call_id = input("Call ID: ").strip().upper()

    # Load port-call records and recover safely from data-loading errors.
    try:
        calls, skipped = data_access.load_port_calls()
    except (FileNotFoundError, ValueError, csv.Error) as error:
        print(f"Error - {error}")
        return

    # Find the port call requested by the user.
    selected_call = None

    for call in calls:
        if call["call_id"] == call_id:
            selected_call = call
            break

    # Stop this service if the Call ID does not exist.
    if selected_call is None:
        print("Port call not found.")
        return

    # Load manifests without allowing a file error to crash the console.
    try:
        manifests, skipped_manifests = data_access.load_manifests()
    except (FileNotFoundError, ValueError, OSError):
        print("Manifest unavailable.")
        return

    # Ensure that the manifest matches both the call ID and vessel ID.
    manifest = operations.find_manifest(manifests, selected_call)

    if manifest is None:
        print("Manifest unavailable.")
        return

    # Verify that event_codes is a list containing only strings.
    # An empty list is valid and produces a sequence of length zero.
    event_codes = manifest["event_codes"]

    if not isinstance(event_codes, list) or not all(
        isinstance(event, str) for event in event_codes
    ):
        print("Manifest unavailable.")
        return

    # Execute the sliding-window algorithm implemented in text_tools.py.
    length, sequence = text_tools.longest_stable_sequence(event_codes)

    # Display the results in the format required by Task 7.
    print(f"Longest stable sequence length: {length}")
    print(f"Sequence: {' -> '.join(sequence)}")

#--------------------------------------------------------------------------------------
# END of Task 7 ------------------
#--------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------
# Start of Task 8 ------------------
#--------------------------------------------------------------------------------------

def run_weather_risk():
    """Task 8: Assess weather risk for upcoming calls."""

    vessel_name = input("Vessel name: ").strip()

    while True:
        date_text = input("Reference date (YYYY-MM-DD): ").strip()

        try:
            reference_date = operations.parse_reference_date(date_text)
            break
        except ValueError:
            print("Error - Date must use YYYY-MM-DD.")

    try:
        vessels, skipped_vessels = data_access.load_vessels()
        calls, skipped_calls = data_access.load_port_calls()
        weather, skipped_weather = data_access.load_weather()

        result = operations.assess_weather_risk(
            vessel_name,
            reference_date,
            vessels,
            calls,
            weather
        )

    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Error assessing weather risk: {error}")
        return

    if result["status"] == "vessel_not_found":
        print("Vessel not found.")
        return

    if result["status"] == "no_upcoming_calls":
        print("No upcoming port calls found.")
        return

    for report in result["reports"]:
        call = report["call"]

        arrival_date = operations.parse_reference_date(
            call["arrival_date"]
        )

        date_display = (
            f"{arrival_date.day} "
            f"{arrival_date.strftime('%B %Y')}"
        )

        print(
            f"\n{vessel_name} | "
            f"{call['port_code']} | "
            f"{date_display}"
        )

        forecast = report["forecast"]

        if forecast is None:
            print("Forecast unavailable.")
            continue

        print(
            f"Wind: {forecast['wind_kmh']:.1f} km/h | "
            f"Rain: {forecast['precipitation_mm']:.1f} mm | "
            f"Waves: {forecast['wave_height_m']:.1f} m"
        )

        print(
            "Recommendation: "
            + " ".join(report["recommendations"])
        )

#--------------------------------------------------------------------------------------
# End of Task 8 ------------------
#--------------------------------------------------------------------------------------
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
