"""Standalone Task 6 service: sanitize an incident report.

This file is completely self-contained — it does not import from any
other task file. Run it directly from the ass2 folder:

    python tests/TEST_CODE/task_06.py            # run the service once
    python tests/TEST_CODE/task_06.py --selftest # run all acceptance checks
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------
# Every line below brings in a tool that is built into Python itself.
# Nothing needs to be installed with pip.
import json
import re
from pathlib import Path
# Path objects represent file-system paths in a way that works on all
# operating systems. "/" between two Path objects joins them into a new path,
# which is much cleaner than concatenating strings with os.sep.


# ---------------------------------------------------------------------------
# Paths — everything is relative to the project root
# ---------------------------------------------------------------------------
# Path(__file__) is this very file.
# .resolve() converts it to a full absolute path with no ".." shortcuts.
# .parents[2] walks up three levels:
#   parents[0] = tests/TEST_CODE  (folder containing this file)
#   parents[1] = tests
#   parents[2] = ass2             (the project root we want)
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# The "/" operator on Path objects joins paths — cleaner than os.path.join().
DATASET_DIRECTORY = PROJECT_ROOT / "data" / "dataset"
INCIDENTS_DIRECTORY = DATASET_DIRECTORY / "incidents"

# All sanitized output files land here. The service creates this directory
# automatically the first time it writes, so it need not exist beforehand.
SANITIZED_DIRECTORY = PROJECT_ROOT / "exports" / "sanitized"

# These four fields must be present and non-empty in every incident record
# for it to be usable by this task.
INCIDENT_REQUIRED_FIELDS = ("incident_id", "call_id", "title", "report")


# ---------------------------------------------------------------------------
# Regular-expression patterns
# ---------------------------------------------------------------------------
# re.compile() converts a pattern string into a compiled Pattern object.
# Compiling once at module load time is faster than recompiling on every call.
#
# The raw string prefix r"..." tells Python not to interpret backslashes as
# escape sequences (like \n for newline). Inside a regex, \b and \d need to
# be real backslash-letter pairs, so raw strings are the standard choice.

# --- Pattern 1: Container identifier (four letters + seven digits) ---
#
# Let us build this pattern piece by piece:
#
#   \b
#     Word boundary. A word character is a letter, digit, or underscore (\w).
#     A non-word character is anything else: space, comma, dot, hyphen, etc.
#     \b matches the invisible edge between a word character and a non-word
#     character. It is "zero-width" — it does not consume any characters.
#
#     Why do we need it?  Without \b, the pattern might match the last four
#     letters and first seven digits of a longer identifier like XMSCU1234567,
#     which would incorrectly redact part of a token that does not qualify.
#     With \b before the first letter, the match can only start where a word
#     begins (i.e. after a space, punctuation, or the start of the string).
#
#   [A-Za-z]{4}
#     A character class [...] matches any single character listed inside.
#     A-Za-z means any letter from A to Z or a to z.
#     {4} is a quantifier meaning "repeat the previous item exactly four
#     times". So [A-Za-z]{4} matches exactly four consecutive letters.
#     Because we pass re.IGNORECASE, [A-Z] would be enough, but both
#     ranges are written here to make the intent obvious.
#
#   \d{7}
#     \d is shorthand for [0-9] — any single digit.
#     {7} means "exactly seven digits".
#
#   \b
#     Closing word boundary. Ensures the seven-digit block is not immediately
#     followed by another word character. This stops MSCU12345678 (eight
#     digits) from being treated as a valid container — the extra '8' keeps
#     the closing boundary from forming, so the match fails.
CONTAINER_PATTERN = re.compile(r"\b[A-Za-z]{4}\d{7}\b", re.IGNORECASE)

# --- Pattern 2: Seal number (SEAL- followed by six digits) ---
#
#   \b      opening word boundary — same reason as above.
#   SEAL    literal text. re.IGNORECASE makes this match "seal", "Seal", etc.
#   -       a literal hyphen. Outside a character class [...], a hyphen has
#           no special regex meaning and simply matches itself.
#   \d{6}   exactly six digits.
#   \b      closing word boundary — stops SEAL-8842100 (seven digits) matching.
SEAL_PATTERN = re.compile(r"\bSEAL-\d{6}\b", re.IGNORECASE)

# --- Pattern 3: Email address ---
#
# Email addresses do not have simple word-character boundaries on all sides
# (the local part can contain dots and plus signs), so \b is not used here.
# The pattern itself is specific enough to avoid false matches.
#
# The spec defines exactly which characters are allowed at each position:
#
#   [A-Za-z0-9._%+\-]+
#     The "local part" before the @ sign. One or more (+) characters that
#     are: a letter (A-Za-z), a digit (0-9), or one of the symbols . _ % + -
#     Inside a character class, a hyphen must be escaped (\-) or placed at
#     the very start or end to avoid being read as a range indicator like A-Z.
#
#   @
#     The literal at-sign. Every email address has exactly one @.
#
#   [A-Za-z0-9.\-]+
#     The domain portion. One or more letters, digits, dots, or hyphens.
#     This can include multiple domain labels separated by dots.
#     Being greedy (+), it first tries to consume as much as possible, then
#     "backtracks" to let the final section below match the last dot + TLD.
#
#   \.
#     A literal dot before the top-level domain. The backslash is essential:
#     without it, a bare . in regex means "match any single character at all"
#     rather than a real period.
#
#   [A-Za-z]{2,}
#     The top-level domain (TLD): at least two letters. {2,} means "two or
#     more". This matches "se", "com", "org", "co", "harborflow", etc.
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")


# ---------------------------------------------------------------------------
# JSON loading helpers
# (same pattern as tasks 1–5; defined locally so this file is standalone)
# ---------------------------------------------------------------------------

def load_json(path):
    """Read one JSON file and return its top-level object as a Python dictionary.

    JSON objects look like: {"key": "value", "number": 42}
    json.load() translates that text into a Python dict automatically.

    Raises:
        FileNotFoundError  — if the file does not exist.
        json.JSONDecodeError — if the file content is not valid JSON.
        ValueError         — if the top-level JSON value is not an object.
    """
    # 'with ... as handle' opens the file and automatically closes it at the
    # end of the indented block, even if an exception is raised inside.
    # encoding="utf-8" makes sure non-ASCII characters are read correctly.
    with Path(path).open("r", encoding="utf-8") as json_file:
        record = json.load(json_file)

    # isinstance(x, dict) asks "is x a Python dictionary?"
    # not reverses the answer: True becomes False and False becomes True.
    # A JSON array ([...]) or scalar would pass json.load() but fail here.
    if not isinstance(record, dict):
        raise ValueError("top-level value must be a JSON object")

    return record


def _validate_incident(record):
    """Check one incident record for missing or empty required fields.

    Returns a human-readable problem string if the record has a flaw,
    or None if every required field is present and non-empty.
    Returning None is a Python convention for "no problem found".
    """
    # Loop through the required field names in order.
    # Checking in order means the first problem found is the one reported,
    # which gives a consistent, predictable message.
    for field in INCIDENT_REQUIRED_FIELDS:
        if field not in record:
            # The key is completely absent from the dictionary.
            return f"{field} is missing"

        value = record[field]

        # isinstance(value, str) checks that the value is a text string.
        # value.strip() removes surrounding whitespace — if only spaces
        # remain after stripping, the field is effectively empty.
        if not isinstance(value, str) or not value.strip():
            return f"{field} must be non-empty text"

    # All required fields were present and non-empty — the record is good.
    return None


def load_incidents(directory):
    """Load every valid incident JSON file from a folder.

    Files are processed in case-insensitive sorted order so repeated runs
    always produce the same results regardless of filesystem ordering.
    One broken file never prevents the others from loading — each is tried
    independently and any problem is recorded as a diagnostic message.

    Returns:
        records     — list of valid incident dicts.
        diagnostics — list of strings describing skipped files.
    """
    directory = Path(directory)

    # is_dir() returns True only when the path exists AND is a folder.
    if not directory.is_dir():
        raise FileNotFoundError(f"Incidents directory not found: {directory}")

    records = []
    diagnostics = []
    seen_ids = set()  # a set stores unique values; used to detect duplicates

    # glob("*.json") finds every filename ending in .json inside the folder.
    # The key= argument to sorted() uses casefold() for case-insensitive order.
    # casefold() is like lower() but handles more international characters.
    for path in sorted(directory.glob("*.json"), key=lambda p: p.name.casefold()):
        try:
            record = load_json(path)

        except FileNotFoundError as error:
            # The file disappeared between glob() listing it and open() reading it.
            diagnostics.append(f"{path.name}: {error}")
            continue  # continue skips the rest of this loop iteration

        except json.JSONDecodeError as error:
            # The file exists but its text is not valid JSON syntax.
            # error.lineno and error.colno pinpoint exactly where parsing broke.
            diagnostics.append(
                f"{path.name}: malformed JSON at line {error.lineno}, column {error.colno}"
            )
            continue

        except ValueError as error:
            # load_json raises ValueError when the top-level value is not a dict.
            diagnostics.append(f"{path.name}: {error}")
            continue

        # Ask our validator whether all required fields are present and valid.
        problem = _validate_incident(record)
        if problem is not None:
            # The record has a field problem — report and skip it.
            diagnostics.append(f"{path.name}: {problem}")
            continue

        # Guard against two files claiming the same incident_id.
        # The first file wins; later duplicates are diagnosed and skipped.
        incident_id = record["incident_id"]
        if incident_id in seen_ids:
            diagnostics.append(f"{path.name}: duplicate incident_id {incident_id}")
            continue

        seen_ids.add(incident_id)   # add() inserts a value into the set
        records.append(record)      # append() adds to the end of the list

    return records, diagnostics


# ---------------------------------------------------------------------------
# Task 6 business logic
# ---------------------------------------------------------------------------

def sanitize_report(text):
    """Apply all three redaction substitutions to the report text.

    Each call to Pattern.sub(replacement, text) is one pass:
      - It finds every non-overlapping match of the compiled pattern.
      - It replaces each matched span with the replacement string.
      - It returns the modified text, leaving everything else unchanged.
      - If nothing matched, it returns the original text unmodified.

    The three passes are applied sequentially:
      1. Container identifiers  → [CONTAINER]
      2. Seal numbers           → [SEAL]
      3. Email addresses        → [EMAIL]

    Because the three patterns are completely disjoint (no container or seal
    can also be an email address), the order of the passes does not affect
    the final result. We use a linear sequence for clarity.

    How do we know whether anything was replaced?
    We compare the final text with the original using !=. If even a single
    character differs, at least one substitution occurred and changed is True.
    This is simpler and more reliable than counting substitutions with a
    separate counter.

    Args:
        text: the original report string.

    Returns:
        (sanitized_text, changed) — a tuple of the (possibly modified) text
        and a boolean that is True when at least one substitution occurred.
    """
    # result starts as a copy of the original and accumulates changes.
    result = text

    # Pass 1 — container identifiers.
    # CONTAINER_PATTERN was compiled with re.IGNORECASE, so MSCU, mscu, MsCu
    # are all treated identically. The [CONTAINER] replacement is a plain
    # string, not a regex, so no escaping is needed inside it.
    result = CONTAINER_PATTERN.sub("[CONTAINER]", result)

    # Pass 2 — seal numbers.
    result = SEAL_PATTERN.sub("[SEAL]", result)

    # Pass 3 — email addresses.
    result = EMAIL_PATTERN.sub("[EMAIL]", result)

    # != means "not equal to". If result and text are the same string,
    # no substitution occurred and changed is False.
    changed = result != text

    # Python allows returning multiple values as a tuple.
    # The caller unpacks them: sanitized_text, changed = sanitize_report(...)
    return result, changed


def sort_incidents(incidents):
    """Return a new list of incidents sorted case-insensitively by title.

    sorted() never modifies the original list — it always creates a new one.
    The key= parameter tells sorted() what value to compare.

    Why casefold() instead of lower()?
    casefold() is a more aggressive form of lower() that handles additional
    Unicode characters. For ASCII text they behave identically, but casefold()
    is the recommended choice for case-insensitive comparisons in Python 3.

    Example sort result for the four supplied incidents:
        1. Gate congestion delay
        2. Reefer temperature deviation
        3. Reefer transfer delayed
        4. Routine inspection completed
    """
    return sorted(incidents, key=lambda incident: incident["title"].casefold())


def write_sanitized_report(incident_id, sanitized_text, output_dir):
    """Write the sanitized text to a file under output_dir.

    The output filename is always:  <incident_id>-sanitized.txt
    The output directory is created automatically when it does not exist.

    Why newline=""?
    When Python opens a text file without newline="", it automatically
    translates the \n characters in the string to the platform's native
    line ending (which is \r\n on Windows). Using newline="" disables this
    translation, preserving the exact characters that came from the original
    report — which is what the spec requires ("preserve every line break").

    Args:
        incident_id:    e.g. "INC-102" — used in the output filename.
        sanitized_text: the redacted report string to write.
        output_dir:     the directory to write into (Path or str).

    Returns:
        The Path of the file that was written.
    """
    output_dir = Path(output_dir)

    # mkdir() creates the directory. parents=True also creates any missing
    # parent directories in one step. exist_ok=True means it is not an error
    # if the directory already exists — the call simply does nothing in that case.
    output_dir.mkdir(parents=True, exist_ok=True)

    # f-strings (f"...") embed variable values directly into a string.
    # {incident_id} is replaced with the actual incident_id value at runtime.
    output_path = output_dir / f"{incident_id}-sanitized.txt"

    # Open the file for writing ("w"), use UTF-8 encoding, and disable
    # automatic newline translation (see docstring above for the reason).
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(sanitized_text)

    return output_path


def service():
    """Run the full Task 6 flow from selection to output.

    The service:
      1. Loads all valid incident records from the incidents folder.
      2. Displays them sorted case-insensitively by title, numbered from 1.
      3. Prompts for a selection number, repeating only the prompt on bad input.
      4. Sanitizes the chosen report using the three regex patterns.
      5. Writes the sanitized file if any substitution occurred, or prints
         the exact no-match message if none did.
    """

    # --- Step 1: Load incidents ---
    # All file and JSON errors that make the whole load impossible are caught
    # here and shown to the user as a clean error message.
    try:
        incidents, _diagnostics = load_incidents(INCIDENTS_DIRECTORY)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        print(f"Error - {error}")
        return   # return exits the function early; control goes back to the menu

    if not incidents:
        # All JSON files in the incidents folder were unreadable or invalid.
        print("No incident reports available.")
        return

    # --- Step 2: Display the sorted title list ---
    # sort_incidents returns a NEW list in title order. The original list is
    # not changed. We keep sorted_incidents for later when the user picks one.
    sorted_incidents = sort_incidents(incidents)

    # enumerate(iterable, start=1) yields (1, first_item), (2, second_item), …
    # start=1 makes the numbering begin at 1 for the user rather than 0.
    for number, incident in enumerate(sorted_incidents, start=1):
        print(f"{number}. {incident['title']}")

    # --- Step 3: Selection prompt loop ---
    # The spec says: for invalid input print the exact error and repeat ONLY
    # the incident-number prompt. We must not re-show the title list or do
    # anything else during a retry — just prompt again.
    while True:
        answer = input("Select incident: ")

        try:
            # int() raises ValueError if the text is not a valid whole number.
            # .strip() removes surrounding whitespace so "  2  " is accepted.
            choice = int(answer.strip())

            # The number must correspond to one of the displayed positions.
            # 1 <= choice <= len(sorted_incidents) checks both boundaries at once.
            if not 1 <= choice <= len(sorted_incidents):
                # Raise ValueError ourselves to reach the same except branch
                # as non-integer input, since both errors use the same message.
                raise ValueError(f"{choice} is not in the displayed list")

            # If we reach this line, choice is a valid 1-based list number.
            break  # break exits the while loop immediately

        except ValueError:
            # Both "abc" (not an integer) and "99" (out of range) land here.
            # The spec mandates exactly this error string — no other wording.
            print("Error - Select a listed incident.")

    # --- Step 4: Retrieve the selected incident ---
    # Python lists are 0-indexed, but the user sees 1-based numbers.
    # Subtracting 1 converts: user's "1" → index 0, "2" → index 1, etc.
    selected = sorted_incidents[choice - 1]

    # --- Step 5: Sanitize the report ---
    # sanitize_report returns a tuple: (new_text, changed_bool)
    sanitized_text, changed = sanitize_report(selected["report"])

    # --- Step 6: Write or report no change ---
    if not changed:
        # The three regex passes found nothing to replace.
        # The spec requires this exact message and explicitly says NOT to
        # create an output file in this case — even if one already exists.
        print("Incident contains no share-sensitive identifiers.")
        return

    # At least one substitution occurred — write the sanitized file.
    try:
        write_sanitized_report(
            selected["incident_id"],
            sanitized_text,
            SANITIZED_DIRECTORY,   # module-level constant; tests override this
        )
    except OSError as error:
        # OSError covers file-system problems like permission denied or disk full.
        print(f"Error - could not write sanitized report: {error}")
        return

    # Inform the user where the output file was saved.
    # We display the path relative to the project root (exports/sanitized/...)
    # rather than the full absolute path, which would be machine-specific.
    print(
        f"Sanitized report saved: "
        f"exports/sanitized/{selected['incident_id']}-sanitized.txt"
    )

if __name__ == "__main__":
    service()

