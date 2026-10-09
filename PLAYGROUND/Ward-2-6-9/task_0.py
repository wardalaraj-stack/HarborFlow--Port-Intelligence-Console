"""Standalone Task 0 console-shell checks for HarborFlow."""

# This file does not re-implement the console. It imports the shared
# application entry point and checks the shell contract with scripted input.

import builtins
import contextlib
import io
import sys
from pathlib import Path


# Walk back to the ass2 folder, then reach src/main.py through the import path.
SRC_DIRECTORY = Path(__file__).resolve().parents[2] / "src"
if str(SRC_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SRC_DIRECTORY))

import main as harborflow_main  # noqa: E402


EXPECTED_MENU = (
    "HARBORFLOW PORT INTELLIGENCE\n"
    "1. List registered vessels\n"
    "2. Inspect a vessel manifest\n"
    "3. Identify priority cargo\n"
    "4. Export a customer operations profile\n"
    "5. Find port calls by month\n"
    "6. Sanitize an incident report\n"
    "7. Analyze the longest stable event sequence\n"
    "8. Assess weather risk for upcoming calls\n"
    "9. Search incident reports\n"
    "10. Close console\n"
    "Select service: "
)
EXPECTED_ERROR = "Error - Select a service from 1 to 10.\n"
EXPECTED_CLOSE = "Console closed. HarborFlow operational data remains safe.\n"


def run_shell(replies):
    """Run main() once, feeding it scripted answers and capturing output."""
    printed = io.StringIO()
    remaining = list(replies)

    def scripted_input(prompt=""):
        # Print the prompt exactly as the real input() call would show it.
        print(prompt, end="", flush=True)
        if not remaining:
            raise AssertionError("main() asked for more input than the scenario supplied")
        return remaining.pop(0)

    saved_input = builtins.input
    builtins.input = scripted_input
    try:
        with contextlib.redirect_stdout(printed):
            harborflow_main.main()
    finally:
        builtins.input = saved_input
    return printed.getvalue()


def expect(label, condition, detail=""):
    """Raise a clear failure when one shell rule does not hold."""
    if not condition:
        raise AssertionError(f"{label} {detail}".strip())


def scenario_menu_and_close():
    text = run_shell(["10"])
    expect("the menu must appear first", text.startswith(EXPECTED_MENU), text)
    expect("the close line must appear once", text.count(EXPECTED_CLOSE) == 1, text)
    expect("option 10 must close cleanly", text.endswith(EXPECTED_CLOSE), text)


def scenario_invalid_text_is_rejected():
    text = run_shell(["abc", "10"])
    expect("text input must be rejected", EXPECTED_ERROR in text, text)
    expect("invalid text must not close the console", text.count(EXPECTED_CLOSE) == 1, text)
    expect("the menu should return after bad text", text.count(EXPECTED_MENU) == 2, text)


def scenario_out_of_range_values_are_rejected():
    text = run_shell(["0", "11", "-1", "10"])
    expect("0 must be rejected", text.count(EXPECTED_ERROR) == 3, text)
    expect("out-of-range values must not close the console", text.count(EXPECTED_CLOSE) == 1, text)
    expect("the menu should reappear after each rejected choice", text.count(EXPECTED_MENU) == 4, text)


def scenario_service_placeholder_returns_to_menu():
    text = run_shell(["1", "10"])
    expect("service 1 should print the placeholder message", "Service not implemented.\n" in text, text)
    expect("the menu should appear again after a service", text.count(EXPECTED_MENU) == 2, text)
    expect("the shell should still close normally", text.endswith(EXPECTED_CLOSE), text)


SCENARIOS = (
    ("menu and close", scenario_menu_and_close),
    ("invalid text", scenario_invalid_text_is_rejected),
    ("out-of-range input", scenario_out_of_range_values_are_rejected),
    ("service placeholder", scenario_service_placeholder_returns_to_menu),
)


def selftest():
    """Run every Task 0 shell check and report the result."""
    failures = 0
    for label, scenario in SCENARIOS:
        try:
            scenario()
        except AssertionError as error:
            failures += 1
            print(f"FAIL  {label}")
            print(f"      {error}")
        else:
            print(f"PASS  {label}")
    print(f"{len(SCENARIOS)} scenarios: {len(SCENARIOS) - failures} passed, {failures} failed")
    if failures:
        raise SystemExit(1)
    return 0


def main(argv=None):
    """Run the Task 0 checks."""
    return selftest()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
