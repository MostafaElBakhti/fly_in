"""
Quick sanity tests for parser.py against the example map from the subject.

Run with: python3 test_parser.py

NOTE: parser.py currently does all its work at *module level* (no main
guard, hardcoded "map.txt" path, no function/class wrapping the parsing
loop). That means importing it immediately runs the whole parse. This
test works around that by just importing it and inspecting `parser.data`
afterward -- but it also means you can't easily re-run parsing on a
different file without editing parser.py itself. Worth fixing later.
"""

import importlib
import sys

failures = []


def check(label, condition):
    if condition:
        print(f"  OK   {label}")
    else:
        print(f"  FAIL {label}")
        failures.append(label)


# --- Run the parser (this executes parser.py's module-level code) ---
import parser as p  # noqa: E402  (must come after map.txt exists in cwd)

data = p.data

print("== Basic fields ==")
check("nb_drones == 5", data.nb_drones == 5)
check("start_hub is not None", data.start_hub is not None)
check("end_hub is not None", data.end_hub is not None)
check("start_hub.name == 'hub'", data.start_hub.name == "hub")
check("end_hub.name == 'goal'", data.end_hub.name == "goal")

print("\n== Zones ==")
check("5 regular zones parsed", len(data.zones) == 5)
zone_names = {z.name for z in data.zones}
check(
    "zone names match expected",
    zone_names == {"roof1", "roof2", "corridorA", "tunnelB", "obstacleX"},
)

corridorA = next((z for z in data.zones if z.name == "corridorA"), None)
check("corridorA found", corridorA is not None)
if corridorA:
    check("corridorA.metadata.zone == 'priority'", corridorA.metadata.zone == "priority")
    check("corridorA.metadata.max_drones == 2", corridorA.metadata.max_drones == 2)
    check("corridorA.metadata.color == 'green'", corridorA.metadata.color == "green")

obstacleX = next((z for z in data.zones if z.name == "obstacleX"), None)
check("obstacleX found", obstacleX is not None)
if obstacleX:
    check("obstacleX.metadata.zone == 'blocked'", obstacleX.metadata.zone == "blocked")

print("\n== zone_by_name lookup dict ==")
check("zone_by_name has 7 entries (5 hubs + start + end)", len(data.zone_by_name) == 7)
check("zone_by_name['hub'] is data.start_hub", data.zone_by_name.get("hub") is data.start_hub)
check("zone_by_name['goal'] is data.end_hub", data.zone_by_name.get("goal") is data.end_hub)
check(
    "zone_by_name['corridorA'] is the same object as in data.zones",
    data.zone_by_name.get("corridorA") is corridorA,
)

print("\n== Connections ==")
check("6 connections parsed", len(data.connections) == 6)

corridorA_tunnelB = next(
    (
        c
        for c in data.connections
        if {c.zone_a.name, c.zone_b.name} == {"corridorA", "tunnelB"}
    ),
    None,
)
check("corridorA-tunnelB connection found", corridorA_tunnelB is not None)
if corridorA_tunnelB:
    check("its max_link_capacity == 2", corridorA_tunnelB.max_link_capacity == 2)

print("\n== Connections resolve to actual Zone objects ==")
if data.connections:
    c = data.connections[0]
    check("connection.zone_a is a Zone instance", isinstance(c.zone_a, p.Zone))
    check(
        "connection.zone_a IS the same object as in zone_by_name (not a copy)",
        c.zone_a is data.zone_by_name.get(c.zone_a.name),
    )

print("\n== Duplicate zone name should raise ValueError ==")
# Call parse_zone directly -- bypassing the loop's bare `except`, which
# would otherwise swallow this and print "not found" instead of failing loud.
try:
    p.parse_zone("hub: roof1 9 9 [zone=normal]")
    check("duplicate name raises ValueError", False)
except ValueError:
    check("duplicate name raises ValueError", True)
except Exception as e:  # noqa: BLE001
    check(f"duplicate name raises ValueError (got {type(e).__name__} instead)", False)


print("\n" + "=" * 40)
if failures:
    print(f"{len(failures)} check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("All checks passed.")