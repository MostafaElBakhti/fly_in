"""Verify the audit checker follows the current subject's movement rules."""
import unittest

from audit_maps import validate
from classes import Connection, Zone, ZoneMetadata
from map import Map


class AuditCheckerTests(unittest.TestCase):
    def setUp(self):
        self.data = Map()
        self.data.nb_drones = 2
        start = Zone("start", 0, 0, ZoneMetadata())
        restricted = Zone(
            "restricted", 1, 0, ZoneMetadata("restricted", max_drones=2),
        )
        goal = Zone("goal", 2, 0, ZoneMetadata())
        self.data.start_hub = start
        self.data.end_hub = goal
        self.data.zone_by_name = {z.name: z for z in (start, restricted, goal)}
        self.data.zones = [restricted]
        self.data.connections = [
            Connection(start, restricted), Connection(restricted, goal),
        ]
        self.data.build_neighbors()

    def test_arrival_frees_link_for_same_turn_departure(self):
        lines = [
            "D1-start-restricted",
            "D1-restricted D2-start-restricted",
            "D1-goal D2-restricted",
            "D2-goal",
        ]
        self.assertEqual(validate(self.data, lines), [])

    def test_rejects_invalid_traces(self):
        traces = [
            ["D1-restricted"],  # restricted movement took only one turn
            ["D1-start-restricted", "D2-start-restricted"],  # late arrival
            ["D1-start-restricted D1-start-restricted"],  # double move
            ["D1-start-restricted D2-start-restricted"],  # link over capacity
            ["D1-goal"],  # no adjacent edge
            ["D3-start-restricted"],  # unknown drone
            ["D1-start-restricted"],  # incomplete delivery
        ]
        for lines in traces:
            with self.subTest(lines=lines):
                self.assertTrue(validate(self.data, lines))

    def test_rejects_zone_overcapacity_and_blocked_destination(self):
        self.data.connections[0].max_link_capacity = 2
        self.data.zone_by_name["restricted"].metadata.max_drones = 1
        lines = [
            "D1-start-restricted D2-start-restricted",
            "D1-restricted D2-restricted",
        ]
        self.assertIn("over capacity", validate(self.data, lines)[0])
        self.data.zone_by_name["restricted"].metadata.zone = "blocked"
        self.assertIn("blocked", validate(self.data, ["D1-restricted"])[0])


if __name__ == "__main__":
    unittest.main()
