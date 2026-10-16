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

# --------------------------------------------------
# Task 4: Customer operations profile
# --------------------------------------------------

def build_customer_profile(shipments, customer_name):
    target = customer_name.strip().casefold()

    matching = []

    for shipment in shipments.values():
        if shipment["customer"].strip().casefold() == target:
            matching.append(shipment)

    if not matching:
        return None

    total_weight = 0.0
    express_count = 0
    destinations = set()

    for shipment in matching:
        total_weight += float(shipment["weight_kg"])

        if shipment["priority"].strip().upper() == "EXPRESS":
            express_count += 1

        destinations.add(shipment["destination"])

    return {
        "customer": matching[0]["customer"],
        "shipment_count": len(matching),
        "total_weight_kg": f"{total_weight:.2f}",
        "express_count": express_count,
        "destinations": "|".join(sorted(destinations)),
    }

# --------------------------------------------------
# Task 4: END
# --------------------------------------------------



# --------------------------------------------------
# Task 8: Weather risk assessment
# --------------------------------------------------

def select_upcoming_calls(calls, vessel_id, reference_date):
    """
    Return (qualifying_calls, invalid_rows).

    qualifying_calls is sorted by arrival date, then call_id.
    invalid_rows contains (line_number, arrival_date) for invalid call dates.
    """
    qualifying = []
    invalid_rows = []

    for line_number, call in enumerate(calls, start=2):
        try:
            arrival = date.fromisoformat(call["arrival_date"])
        except ValueError:
            invalid_rows.append((line_number, call["arrival_date"]))
            continue

        if call["vessel_id"] != vessel_id:
            continue

        if arrival >= reference_date:
            qualifying.append((arrival, call["call_id"], call))

    qualifying.sort(key=lambda item: (item[0], item[1]))

    return [item[2] for item in qualifying], invalid_rows

def build_weather_lookup(weather_rows):
    """
    Return (lookup, malformed_rows).

    A valid forecast is keyed by (port_code, date).
    Malformed numeric rows are reported and skipped.
    """
    lookup = {}
    malformed_rows = []

    for line_number, row in enumerate(weather_rows, start=2):
        try:
            wind = float(row["wind_kmh"])
            rain = float(row["precipitation_mm"])
            waves = float(row["wave_height_m"])
        except ValueError:
            malformed_rows.append((line_number, row))
            continue

        key = (row["port_code"], row["date"])

        if key not in lookup:
            lookup[key] = {
                "wind_kmh": wind,
                "precipitation_mm": rain,
                "wave_height_m": waves,
            }

    return lookup, malformed_rows


def weather_recommendations(wind_kmh, precipitation_mm, wave_height_m):
    """Return every recommendation whose condition is true, in table order."""
    recommendations = []

    if wind_kmh >= 45:
        recommendations.append("Suspend crane operations.")

    if wave_height_m >= 2.5:
        recommendations.append("Arrange tug assistance.")

    if precipitation_mm >= 8 and wind_kmh < 45:
        recommendations.append("Prepare covered handling.")

    if not recommendations:
        recommendations.append("Normal operating plan.")

    return recommendations


def assess_weather_risk(vessel_name, reference_date, vessels, calls, weather_rows):
    """
    Build Task 8 results without printing.

    Returns a dictionary with status, invalid/malformed diagnostics, and reports.
    """
    vessel = find_vessel_by_name(vessel_name, vessels)

    if vessel is None:
        return {
            "status": "vessel_not_found",
            "invalid_calls": [],
            "malformed_forecasts": [],
            "reports": [],
        }

    upcoming, invalid_calls = select_upcoming_calls(
        calls,
        vessel["vessel_id"],
        reference_date,
    )

    if not upcoming:
        return {
            "status": "no_upcoming_calls",
            "invalid_calls": invalid_calls,
            "malformed_forecasts": [],
            "reports": [],
        }

    weather_lookup, malformed_forecasts = build_weather_lookup(weather_rows)
    reports = []

    for call in upcoming:
        forecast = weather_lookup.get((call["port_code"], call["arrival_date"]))

        if forecast is None:
            reports.append({
                "call": call,
                "forecast": None,
                "recommendations": [],
            })
            continue

        recommendations = weather_recommendations(
            forecast["wind_kmh"],
            forecast["precipitation_mm"],
            forecast["wave_height_m"],
        )

        reports.append({
            "call": call,
            "forecast": forecast,
            "recommendations": recommendations,
        })

    return {
        "status": "ok",
        "invalid_calls": invalid_calls,
        "malformed_forecasts": malformed_forecasts,
        "reports": reports,
    }
