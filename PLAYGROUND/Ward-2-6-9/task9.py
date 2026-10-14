"""Task 9: Search incident reports.

This is a standalone Ward submission file. It reuses the pre-existing
HarborFlow data-access helpers from src/data_access.py whenever they are
available, and otherwise keeps the cache and search behavior self-contained.
"""

# Add the project root to sys.path before importing project modules.
import sys  # Python module/path control.
from pathlib import Path  # Cross-platform paths.

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # Repository root.
if str(PROJECT_ROOT) not in sys.path:  # Make project modules importable.
    sys.path.insert(0, str(PROJECT_ROOT))  # Add project root.

# Import pre-existing HarborFlow data helpers when they exist.
try:
    import src.data_access as data_access  # Pre-existing loader/path helper.
except Exception:  # Fall back to a directly importable data_access module.
    try:
        import data_access  # Alternate import location.
    except Exception as import_error:  # No data module is available.
        raise ImportError("Could not import data_access from src or project root") from import_error

# Import JSON support for reading and writing the incident index cache.
import json  # JSON parser and serializer.

# Import operating-system helpers for file replacement and temp-file cleanup.
import os  # OS-level filesystem helpers.

# Import regular expressions for text normalization.
import re  # Regular-expression support.

# Import temporary-file helper for atomic cache writes.
import tempfile  # Creates temporary files.

# Reuse the pre-existing module's configured incident source directory when possible.
INCIDENTS_DIR = PROJECT_ROOT / "dataset" / "incidents"  # Path to dataset/incidents.

# Reuse the pre-existing module's configured cache file path when possible.
INCIDENT_INDEX_FILE = PROJECT_ROOT / "dataset" / "incident-index.json"  # Path to cache file.

# List required incident fields for validation.
INCIDENT_REQUIRED_FIELDS = ("incident_id", "call_id", "title", "report")  # Required incident JSON fields.

# Compile the tokenizer once for repeated normalization calls.
TOKEN_PATTERN = re.compile(r"[^\W_]+", flags=re.UNICODE)  # Unicode word tokenizer.


def normalize_words(text):  # Normalize report text or a query into search words.
    if text is None:  # Guard against None input.
        return []  # Return no words for None.

    if not isinstance(text, str):  # Convert non-string input to a string.
        text = str(text)  # Convert the value.

    return TOKEN_PATTERN.findall(text.casefold())  # Lowercase and extract word tokens.


# Compatibility aliases for the shared tokenizer.
normalize_text = normalize_words  # Alias for older expected name.
normalize_query = normalize_words  # Alias for query normalization.
tokenize = normalize_words  # Alias for tokenizer name.
tokenize_text = normalize_words  # Alias for text tokenizer name.


def validate_incident_records(incidents):  # Extract valid incident records from input.
    if isinstance(incidents, tuple) and len(incidents) == 2 and isinstance(
            incidents[0], (dict, list, tuple)):  # Detect (records, skipped) tuple input.
        incidents = incidents[0]  # Unpack records from tuple.

    if isinstance(incidents, dict):  # Input is a mapping of incidents.
        records = list(incidents.values())  # Use dictionary values as records.

    elif isinstance(incidents, (list, tuple)):  # Input is a list or tuple.
        records = list(incidents)  # Convert iterable to a list.

    else:  # Input type is unsupported.
        raise TypeError("incidents must be a mapping or iterable of records")  # Raise invalid type error.

    valid = []  # Accumulate valid incident records.
    
    for record in records:  # Inspect every supplied record.
        if not isinstance(record, dict):  # Skip non-dictionary records.
            continue  # Move to the next record.

        if any(field not in record for field in INCIDENT_REQUIRED_FIELDS):  # Find missing required fields.
            continue  # Skip records with missing fields.

        if not all(  # Validate each required string field.
                isinstance(record[field], str) and record[field].strip()  # Check string and non-empty.
                for field in INCIDENT_REQUIRED_FIELDS):  # Check all required fields.
            continue  # Skip records with invalid fields.

        valid.append(record)  # Keep valid records.

    return valid  # Return valid records.


def load_incidents(directory=None):  # Load incidents using existing data_access helper.
    if directory is None:  # Use default source directory when omitted.
        directory = INCIDENTS_DIR  # Assign default incident directory.

    return data_access.load_incidents(directory)  # Delegate to unchanged loader.


def discover_incident_source_paths(directory=None):  # Discover and stat all source files.
    if directory is None:  # Use default source directory when omitted.
        directory = INCIDENTS_DIR  # Assign default incident directory.

    directory = Path(directory)  # Convert path to Path object.
    if not directory.is_dir():  # Check that source directory exists.
        raise FileNotFoundError(
            f"incident source directory not found: {directory}")  # Raise missing directory error.

    paths = sorted(  # Sort source files deterministically.
        directory.glob("*.json"),  # Find incident JSON files.
        key=lambda item: (item.name.casefold(), str(item)))  # Sort by case-insensitive filename.
    if not paths:  # Check that at least one source exists.
        raise ValueError(f"no incident source files found in {directory}")  # Raise empty source list error.

    for path in paths:  # Stat every source file.
        path.stat()  # Raise if a file cannot be accessed.

    return paths  # Return sorted source paths.


# Compatibility aliases for source discovery.
discover_incident_files = discover_incident_source_paths  # Alias for discovery.
list_incident_source_paths = discover_incident_source_paths  # Alias for discovery.
get_incident_source_paths = discover_incident_source_paths  # Alias for discovery.
incident_source_paths = discover_incident_source_paths  # Alias for discovery.
incident_source_files = discover_incident_source_paths  # Alias for discovery.
list_incident_files = discover_incident_source_paths  # Alias for discovery.


def is_valid_incident_index_cache(data):  # Validate cache shape and value types only.
    if not isinstance(data, dict):  # Cache must be a dictionary.
        return False  # Invalid cache.

    if set(data.keys()) != {"index", "titles"}:  # Require exact top-level keys.
        return False  # Invalid cache.

    index = data.get("index")  # Get inverted index object.
    titles = data.get("titles")  # Get title lookup object.
    if not isinstance(index, dict) or not isinstance(titles, dict):  # Both must be dictionaries.
        return False  # Invalid cache.

    for key, value in index.items():  # Validate each index entry.
        if not isinstance(key, str):  # Word keys must be strings.
            return False  # Invalid cache.

        if not isinstance(value, list) or not all(  # Posting values must be lists of strings.
                isinstance(item, str) for item in value):  # Check every incident ID string.
            return False  # Invalid cache.

    for key, value in titles.items():  # Validate each title entry.
        if not isinstance(key, str) or not isinstance(value, str):  # Keys and titles must be strings.
            return False  # Invalid cache.

    return True  # Cache passes basic shape validation.


def cache_is_fresh(cache_path, source_paths):  # Compare cache age with source files.
    cache_path = Path(cache_path)  # Convert cache path to Path.
    try:  # Attempt to stat cache file.
        cache_mtime = cache_path.stat().st_mtime  # Read cache modification time.
    except FileNotFoundError:  # Cache is missing.
        return False  # Missing cache is not fresh.

    for source_path in source_paths:  # Compare against every source.
        if cache_mtime < Path(source_path).stat().st_mtime:  # Check cache age.
            return False  # Cache is older than a source file.

    return True  # Cache is not older than any source file.


# Compatibility aliases for cache validation and freshness.
validate_incident_cache = is_valid_incident_index_cache  # Alias for validation.
is_valid_cache = is_valid_incident_index_cache  # Alias for validation.
is_cache_valid = is_valid_incident_index_cache  # Alias for validation.
cache_is_valid = is_valid_incident_index_cache  # Alias for validation.

is_cache_fresh = cache_is_fresh  # Alias for freshness.
is_incident_cache_fresh = cache_is_fresh  # Alias for freshness.
incident_cache_is_fresh = cache_is_fresh  # Alias for freshness.
cache_fresh = cache_is_fresh  # Alias for freshness.


def read_incident_index(path=None):  # Read cache JSON from disk.
    if path is None:  # Use default cache path when omitted.
        path = INCIDENT_INDEX_FILE  # Assign default cache file.

    path = Path(path)  # Convert path to Path object.
    with path.open("r", encoding="utf-8") as handle:  # Open cache for reading.
        return json.load(handle)  # Parse and return cache content.


def write_incident_index(path=None, data=None):  # Write cache atomically.
    if path is None:  # Use default cache path when omitted.
        path = INCIDENT_INDEX_FILE  # Assign default cache file.

    path = Path(path)  # Convert path to Path object.
    path.parent.mkdir(parents=True, exist_ok=True)  # Ensure dataset directory exists.

    descriptor, temporary_name = tempfile.mkstemp(  # Create temp file in cache directory.
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))  # Name the temporary file.
    temporary_path = Path(temporary_name)  # Store temporary path.
    try:  # Protect temporary/cache operation.
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:  # Open temp file.
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)  # Write sorted JSON.
            handle.write("\n")  # Add final newline.
            handle.flush()  # Flush written content.
            os.fsync(handle.fileno())  # Force data to disk.
        os.replace(temporary_path, path)  # Atomically replace cache file.
    except BaseException:  # Catch any write/replace failure.
        try:  # Attempt temporary-file cleanup.
            temporary_path.unlink()  # Remove partial temporary file.
        except FileNotFoundError:  # Ignore already-removed temp file.
            pass  # Nothing more to clean.
        raise  # Re-raise original error.
    return path  # Return cache file path.


# Compatibility aliases for cache reading and writing.
read_cache = read_incident_index  # Alias for cache read.
read_incident_cache = read_incident_index  # Alias for cache read.
load_incident_index = read_incident_index  # Alias for cache read.
load_incident_cache = read_incident_index  # Alias for cache read.

write_cache = write_incident_index  # Alias for cache write.
write_incident_cache = write_incident_index  # Alias for cache write.
save_incident_index = write_incident_index  # Alias for cache write.
save_incident_cache = write_incident_index  # Alias for cache write.


def build_incident_index(incidents):  # Build inverted index and title lookup.
    records = validate_incident_records(incidents)  # Validate supplied records.
    if not records:  # Ensure there is source data.
        raise ValueError("No valid incident reports available for indexing")  # Raise if no records.

    index = {}  # Map words to incident ID sets.
    titles = {}  # Map incident IDs to titles.
    seen_ids = set()  # Track duplicate incident IDs.

    for record in records:  # Inspect each valid record.
        incident_id = record["incident_id"].strip()  # Read incident ID.
        if incident_id in seen_ids:  # Skip duplicate incident IDs.
            continue  # Use first record only.

        seen_ids.add(incident_id)  # Mark this incident ID seen.
        titles[incident_id] = record["title"]  # Store title for this incident.

        for word in set(normalize_words(record["report"])):  # Normalize and deduplicate report words.
            index.setdefault(word, set()).add(incident_id)  # Add incident ID once per word.

    normalized_index = {  # Convert posting sets to sorted lists.
        word: sorted(ids) for word, ids in index.items()  # Sort each incident ID list.
    }
    return {  # Return assignment-shaped cache.
        "index": {word: normalized_index[word]  # Sorted word keys and sorted lists.
                  for word in sorted(normalized_index)},  # Sort all word keys.
        "titles": {incident_id: titles[incident_id]  # Sorted title keys.
                    for incident_id in sorted(titles)},  # Sort all incident IDs.
    }


# Common build aliases.
build_index = build_incident_index  # Alias for build_incident_index.
build_incident_cache = build_incident_index  # Alias for build_incident_index.
create_incident_index = build_incident_index  # Alias for build_incident_index.
make_incident_index = build_incident_index  # Alias for build_incident_index.


def search_incident_index(cache, query):  # Score incidents using only cache data.
    if not isinstance(cache, dict):  # Validate cache object.
        raise TypeError("cache must be a dictionary")  # Raise invalid cache type.

    index = cache.get("index")  # Fetch inverted index.
    if not isinstance(index, dict):  # Validate index object.
        index = {}  # Fall back to empty index.

    titles = cache.get("titles")  # Fetch title lookup.
    if not isinstance(titles, dict):  # Validate title lookup.
        titles = {}  # Fall back to empty titles.

    query_words = list(dict.fromkeys(normalize_words(query)))  # Normalize and deduplicate query words.

    scores = {}  # Accumulate incident scores.
    for word in query_words:  # Score each distinct query word.
        posting = index.get(word)  # Fetch IDs containing the word.
        if not isinstance(posting, list):  # Skip invalid posting lists.
            continue  # Move to the next query word.

        for incident_id in posting:  # Inspect each posted incident ID.
            if isinstance(incident_id, str):  # Only score string IDs.
                scores[incident_id] = scores.get(incident_id, 0) + 1  # Add one point.

    results = [  # Keep only positive scores.
        (incident_id, score)  # Store ID and score tuple.
        for incident_id, score in scores.items()  # Iterate scored incidents.
        if score > 0  # Omit zero-score incidents.
    ]
    results.sort(key=lambda item: (-item[1], item[0]))  # Sort by score desc then ID asc.
    return results  # Return ranked results.


# Common search aliases.
search_incidents = search_incident_index  # Alias for search_incident_index.
search_incident_reports = search_incident_index  # Alias for search_incident_index.
search_cache = search_incident_index  # Alias for search_incident_index.
rank_incidents = search_incident_index  # Alias for search_incident_index.
score_incidents = search_incident_index  # Alias for search_incident_index.
rank_incident_search = search_incident_index  # Alias for search_incident_index.


def load_or_build_incident_index(directory=None, cache_path=None):  # Load or rebuild cache.
    if directory is None:  # Use default source directory when omitted.
        directory = INCIDENTS_DIR  # Assign default incident directory.

    if cache_path is None:  # Use default cache path when omitted.
        cache_path = INCIDENT_INDEX_FILE  # Assign default cache file.

    source_paths = discover_incident_source_paths(directory)  # Discover all source files.
    cache = None  # Cache result starts empty.
    cache_loaded = False  # Reuse flag starts false.

    try:  # Attempt to read an existing cache.
        candidate = read_incident_index(cache_path)  # Read cache candidate.
    except FileNotFoundError:  # Handle missing cache.
        candidate = None  # Mark candidate unavailable.
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError, TypeError):  # Handle malformed/wrong cache.
        candidate = None  # Mark candidate unusable.
    else:  # Continue only if read succeeded.
        if is_valid_incident_index_cache(candidate) and cache_is_fresh(  # Validate shape and freshness.
                cache_path, source_paths):  # Check cache age.
            cache = candidate  # Reuse candidate.
            cache_loaded = True  # Mark cache loaded.

    if not cache_loaded:  # Rebuild when cache was not loaded.
        records, _skipped = load_incidents(directory)  # Load source records.
        if not records:  # Require at least one valid source record.
            raise ValueError("No valid incident reports available for indexing")  # Fail explicit.

        cache = build_incident_index(records)  # Build cache from source records.
        write_incident_index(cache_path, cache)  # Save rebuilt cache.

    return cache  # Return loaded or rebuilt cache.


# Compatibility aliases around loading/caching.
load_or_build_incident_cache = load_or_build_incident_index  # Alias for loader.
load_incident_index_cache = load_or_build_incident_index  # Alias for loader.
get_incident_index = load_or_build_incident_index  # Alias for loader.
get_incident_cache = load_or_build_incident_index  # Alias for loader.


def run_search_incidents():  # Run one Task 9 search interaction.
    try:  # Wrap cache loading for clean errors.
        cache = load_or_build_incident_index(INCIDENTS_DIR, INCIDENT_INDEX_FILE)  # Load or rebuild cache.
    except (FileNotFoundError, ValueError, OSError, TypeError, KeyError,  # Expected failure types.
            json.JSONDecodeError, UnicodeDecodeError) as error:  # Unexpected but handled errors.
        print(f"Error - {error}")  # Print clean error message.
        return  # Stop search.

    query = input("Search incident reports: ")  # Prompt for query.
    normalized = normalize_words(query)  # Normalize query words.
    if not normalized:  # Handle query with no searchable words.
        print("Search query contains no searchable words.")  # Print required message.
        return  # Stop search.

    results = search_incident_index(cache, query)  # Score query from cache.

    print(f"Matches for '{query}':")  # Print required heading.
    titles = cache.get("titles", {}) if isinstance(cache, dict) else {}  # Fetch title lookup.
    if not results:  # Handle no positive matches.
        print("No matching incidents found.")  # Print required message.
        return  # Stop search.

    for incident_id, score in results:  # Print each positive match.
        title = titles.get(incident_id, "") if isinstance(titles, dict) else ""  # Read cached title.
        print(f"- {incident_id} | score {score} | {title}")  # Print required match line.


def main():  # Module entry point.
    run_search_incidents()  # Run search when file is executed.


if __name__ == "__main__":  # Check direct execution.
    main()  # Call main function.
