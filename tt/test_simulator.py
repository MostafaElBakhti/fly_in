"""Run with: python3 -m unittest discover -s tt -p 'test_*.py' -v."""

import contextlib
import io
import unittest
from collections import Counter
from pathlib import Path

from classes import Connection, Zone, ZoneMetadata
from map import Map
from parser import parse_map_file
from simulator import DeadlockError, Simulator


MAPS = Path(__file__).resolve().parent / "maps"
TARGETS = {
    "easy/01_linear_path.txt": 6,
    "easy/02_simple_fork.txt": 8,
    "easy/03_basic_capacity.txt": 6,
    "medium/01_dead_end_trap.txt": 12,
    "medium/02_circular_loop.txt": 15,
    "medium/03_priority_puzzle.txt": 12,
    "hard/01_maze_nightmare.txt": 30,
    "hard/02_capacity_hell.txt": 35,
    "hard/03_ultimate_challenge.txt": 45,
    "challenger/01_the_impossible_dream.txt": 45,
}


class SimulatorTests(unittest.TestCase):
    """Replay printed moves without using simulator state transitions."""

    def check_trace(self, data: Map, output: str) -> int:
        """Validate simultaneous moves, restricted timing, and capacities."""
        assert data.start_hub is not None
        assert data.end_hub is not None
        start = data.start_hub.name
        goal = data.end_hub.name
        # A position is a zone name or a (source, destination) transit tuple.
        positions: dict[str, str | tuple[str, str]] = {
            f"D{i}": start for i in range(1, data.nb_drones + 1)
        }
        capacities = {
            frozenset((edge.zone_a.name, edge.zone_b.name)):
            edge.max_link_capacity
            for edge in data.connections
        }
        lines = output.splitlines()
        self.assertTrue(lines, "missing movement output")

        for turn, line in enumerate(lines, 1):
            self.assertTrue(
                any(position != goal for position in positions.values()),
                f"turn {turn}: extra output after delivery",
            )
            self.assertEqual(line, line.strip())
            self.assertNotIn("  ", line)
            actions: dict[str, list[str]] = {}
            for token in line.split():
                self.assertRegex(token, r"^D[1-9]\d*-[^-\s]+(?:-[^-\s]+)?$")
                drone, *movement_parts = token.split("-")
                self.assertIn(drone, positions)
                self.assertNotIn(drone, actions, f"turn {turn}: double move")
                actions[drone] = movement_parts

            next_positions = dict(positions)
            link_usage: Counter[frozenset[str]] = Counter()
            for drone, position in positions.items():
                action = actions.get(drone)
                if isinstance(position, tuple):
                    source, destination = position
                    self.assertEqual(
                        action, [destination],
                        f"turn {turn}: {drone} must finish restricted travel",
                    )
                    # Arrival uses the link for the second movement turn.
                    link_usage[frozenset(position)] += 1
                    next_positions[drone] = destination
                    continue

                if action is None:
                    continue
                self.assertNotEqual(position, goal, "delivered drone moved")
                destination = action[-1]
                self.assertIn(destination, data.zone_by_name)
                edge = frozenset((position, destination))
                self.assertIn(edge, capacities, "move uses a missing edge")
                zone_type = data.zone_by_name[destination].metadata.zone
                self.assertNotEqual(zone_type, "blocked")
                if len(action) == 2:
                    self.assertEqual(action[0], position)
                    self.assertEqual(zone_type, "restricted")
                    next_positions[drone] = (position, destination)
                else:
                    self.assertNotEqual(zone_type, "restricted")
                    next_positions[drone] = destination
                link_usage[edge] += 1

            for edge, usage in link_usage.items():
                self.assertLessEqual(
                    usage, capacities[edge],
                    f"turn {turn}: link {sorted(edge)} over capacity",
                )
            occupancy = Counter(
                position for position in next_positions.values()
                if isinstance(position, str)
            )
            for name, count in occupancy.items():
                if name not in (start, goal):
                    self.assertLessEqual(
                        count, data.zone_by_name[name].metadata.max_drones,
                        f"turn {turn}: zone {name} over capacity",
                    )
            positions = next_positions

        self.assertTrue(
            all(position == goal for position in positions.values()),
            "trace ended before every drone arrived",
        )
        return len(lines)

    def run_checked(self, data: Map, paths: list) -> tuple[Simulator, str]:
        """Capture the public runner and check its complete printed trace."""
        simulation = Simulator(data, paths)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            simulation.run()
        trace = output.getvalue()
        turns = self.check_trace(data, trace)
        self.assertEqual(turns, simulation.history[-1]["turn"])
        self.assertTrue(all(drone.finished for drone in simulation.drones))
        return simulation, trace

    def test_all_maps_meet_targets_with_valid_repeatable_output(self) -> None:
        """All supplied maps must produce valid output within their targets."""
        filenames = sorted(MAPS.rglob("*.txt"))
        self.assertEqual(
            {str(filename.relative_to(MAPS)) for filename in filenames},
            set(TARGETS),
        )
        for filename in filenames:
            name = str(filename.relative_to(MAPS))
            with self.subTest(map=name):
                data = parse_map_file(filename)
                simulation, trace = self.run_checked(
                    data, data.find_all_paths(max_paths=5),
                )
                turns = simulation.history[-1]["turn"]
                self.assertLessEqual(turns, TARGETS[name])
                fresh_data = parse_map_file(filename)
                _, repeated_trace = self.run_checked(
                    fresh_data, fresh_data.find_all_paths(max_paths=5),
                )
                self.assertEqual(trace, repeated_trace)

    @staticmethod
    def restricted_map(drones: int, capacity: int) -> Map:
        """Build a simple route with space at the restricted destination."""
        data = Map()
        data.nb_drones = drones
        data.start_hub = Zone("start", 0, 0, ZoneMetadata())
        restricted = Zone("restricted", 1, 0, ZoneMetadata(
            "restricted", max_drones=drones,
        ))
        data.end_hub = Zone("goal", 2, 0, ZoneMetadata())
        data.zones = [restricted]
        data.zone_by_name = {
            zone.name: zone
            for zone in (data.start_hub, restricted, data.end_hub)
        }
        data.connections = [
            Connection(data.start_hub, restricted, capacity),
            Connection(restricted, data.end_hub, capacity),
        ]
        data.build_neighbors()
        return data

    def test_restricted_arrival_cannot_move_again(self) -> None:
        """A two-turn arrival must be followed by a separate departure turn."""
        data = self.restricted_map(1, 1)
        _, output = self.run_checked(data, data.find_all_paths())
        self.assertEqual(
            output, "D1-start-restricted\nD1-restricted\nD1-goal\n",
        )

    def test_link_capacity_applies_to_both_restricted_turns(self) -> None:
        """A capacity-two link permits two starts, then two arrivals."""
        data = self.restricted_map(4, 2)
        simulation, output = self.run_checked(data, data.find_all_paths())
        self.assertEqual(simulation.history[-1]["turn"], 5)
        self.assertEqual(output.splitlines()[:2], [
            "D1-start-restricted D2-start-restricted",
            "D1-restricted D2-restricted",
        ])

    def test_validator_rejects_invalid_restricted_traces(self) -> None:
        """Ensure the checker catches the previous timing/capacity mistakes."""
        data = self.restricted_map(2, 1)
        invalid_traces = [
            # A drone arrives and leaves in one turn.
            "D1-start-restricted\nD1-restricted D1-goal\n",
            # A restricted destination is reached in one turn.
            "D1-restricted\n",
            # D2 departs while D1 is still using the same link to arrive.
            "D1-start-restricted\nD1-restricted D2-start-restricted\n",
            # D1 waits on a connection instead of arriving next turn.
            "D1-start-restricted\n\n",
        ]
        for trace in invalid_traces:
            with self.subTest(trace=trace), self.assertRaises(AssertionError):
                self.check_trace(data, trace)

    def test_deadlocked_candidate_is_skipped(self) -> None:
        """Opposing assigned routes must not hang the route-set comparison."""
        data = Map()
        data.nb_drones = 2
        zones = [Zone(name, i, 0, ZoneMetadata())
                 for i, name in enumerate(("start", "a", "b", "goal"))]
        start, a, b, goal = zones
        data.start_hub, data.end_hub = start, goal
        data.zones = [a, b]
        data.zone_by_name = {zone.name: zone for zone in zones}
        data.connections = [Connection(source, destination) for
                            source, destination in (
                                (start, a), (start, b), (a, b),
                                (a, goal), (b, goal),
                            )]
        data.build_neighbors()
        paths = [[start, a, b, goal], [start, b, a, goal]]
        trial = Simulator(data, paths)
        trial.assign_paths()
        with self.assertRaises(DeadlockError):
            trial._simulate(emit_output=False)
        simulation, _ = self.run_checked(data, paths)
        self.assertEqual(len(simulation.paths), 1)
        self.assertEqual(simulation.history[-1]["turn"], 4)


if __name__ == "__main__":
    unittest.main()
