"""Pure business rules for HarborFlow services."""

from datetime import date

# ---------------------------------------------------------------------------
#task_02 starts here - Vessel and manifest operations 
#-----------------------------------------------------------------------

def find_vessel_by_name(name, vessels):
    wanted_vessel = name.strip().casefold()

    for vessel in vessels.values():
        if vessel["name"].strip().casefold() == wanted_vessel:
            return vessel

    return None


def parse_reference_date(value):
    
    value = value.strip()

    if len(value) != 10 or value[4] != "-" or value[7] != "-":
        raise ValueError("invalid date shape")

    if not (value[:4] + value[5:7] + value[8:]).isdigit():
        raise ValueError("invalid date shape")

    return date.fromisoformat(value)


def select_upcoming_call(calls, vessel_id, reference_date):
    """Return the earliest valid call on or after the reference date.
    from port_calls.csv."""

    candidates = []

    for call in calls:
        if call["vessel_id"] != vessel_id:
            continue

        try:
            arrival_date = date.fromisoformat(call["arrival_date"])
            #.fromisoformat means the date string must be in YYYY-MM-DD format
        except ValueError:
            continue

        if arrival_date >= reference_date:
            candidates.append((arrival_date, call["call_id"], call))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (item[0], item[1]))
    return candidates[0][2]


def find_manifest(manifests, call):
    """Return the manifest matching both the call and vessel identifiers."""
    manifest = manifests.get(call["call_id"])
    # Ensure the manifest exists and matches the vessel before returning it


    if manifest is None or manifest["vessel_id"] != call["vessel_id"]:
        return None

    return manifest


def build_manifest_report(vessel, call, manifest, shipments):
    """Build an ordered Task 2 report without printing."""
    lines = []
    resolved_weight = 0.0
    missing = 0

    arrival_date = date.fromisoformat(call["arrival_date"])
    date_display = f"{arrival_date.day} {arrival_date.strftime('%B %Y')}"
    # .strftime('%B %Y') gives the full month name and year


    for shipment_id in manifest["shipment_ids"]:
        shipment = shipments.get(shipment_id)

        if shipment is None:
            lines.append({
                "resolved": False,
                "shipment_id": shipment_id,
            })
            missing += 1
            continue

        cargo_type = shipment.get("cargo_type")
        if cargo_type is None:
            cargo_type = "NOT PROVIDED"

        lines.append({
            "resolved": True,
            "shipment_id": shipment["shipment_id"],
            "customer": shipment["customer"],
            "weight_kg": shipment["weight_kg"],
            "cargo_type": cargo_type,
        })
        resolved_weight += shipment["weight_kg"]

    return {
        "vessel_name": vessel["name"],
        "call_id": call["call_id"],
        "date_display": date_display,
        "lines": lines,
        "declared": len(manifest["shipment_ids"]),
        "resolved_weight": resolved_weight,
        "missing": missing,
    }

# ---------------------------------------------------------------------------
#task_02 ends here - Vessel and manifest operations 
#-----------------------------------------------------------------------
# ---------------------------------------------------------------------------
#task_03 starts here - Identify Priority Cargo
#-----------------------------------------------------------------------

"""
What the output should look like:

ship_id, categorization (first shown), ?????
then Category totals...etc etc (list them all even if 0)

SHP-1045 | EXPEDITE | express service
SHP-1046 | CONTROLLED | hazardous cargo
SHP-1067 | EXPEDITE | express service
Category totals: CONTROLLED=1, COLD CHAIN=0, EXPEDITE=2, STANDARD=0

"""

# ---------------------------------------------------------------------------
#task_03 ends here - Identify Priority Cargo
#-----------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Task 5 Start here - Find port calls by month
# ---------------------------------------------------------------------------

def parse_call_date(arrival_date):
    """Validate a port-call date and return a Python date object."""

    # Reuse the existing date-format and calendar validation.
    call_date = parse_reference_date(arrival_date)

    return call_date

def collect_month_calls(month, records, vessel_by_id):
    """Return calls for the selected month and problems with rejected rows."""

    matching_calls = []
    issues = []

    for record in records:
        try:
            call_date = parse_call_date(record["arrival_date"])
        except ValueError:
            # Reject invalid dates without stopping later rows.
            issues.append(
                (record["call_id"],
                 f"invalid arrival_date '{record['arrival_date']}'")
            )
        else:
            vessel_id = record["vessel_id"]

            if vessel_id not in vessel_by_id:
                # A call must refer to a known vessel.
                issues.append(
                    (record["call_id"],
                     f"unknown vessel_id '{vessel_id}'")
                )
            else:
                vessel = vessel_by_id[vessel_id]

                # Match the selected month, regardless of the year.
                if call_date.month == month:
                    matching_calls.append({
                        "call_date": call_date,
                        "vessel_name": vessel["name"],
                        "port_code": record["port_code"],
                        "call_id": record["call_id"],
                    })

    # Sort by date, then vessel name; call ID resolves remaining ties.
    matching_calls.sort(
        key=lambda record: (
            record["call_date"],
            record["vessel_name"].casefold(),
            record["call_id"],
        )
    )

    return matching_calls, issues

# ---------------------------------------------------------------------------
# Task 5 ends here - Find port calls by month
# ---------------------------------------------------------------------------
