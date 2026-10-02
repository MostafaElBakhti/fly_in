"""Run with: python3 -m unittest discover -s . -p 'test_*.py' -v."""

import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from classes import Connection, Zone, ZoneMetadata
from map import Map
from parser import parse_map_file
from simulator import DeadlockError, Simulator


MAPS = Path(__file__).resolve().parent / "maps"
TARGETS = {
    "easy/01_linear_path.txt": 4,
    "easy/02_simple_fork.txt": 4,
    "easy/03_basic_capacity.txt": 4,
    "medium/01_dead_end_trap.txt": 8,
    "medium/02_circular_loop.txt": 10,
    "medium/03_priority_puzzle.txt": 6,
    "hard/01_maze_nightmare.txt": 13,
    "hard/02_capacity_hell.txt": 16,
    "hard/03_ultimate_challenge.txt": 26,
    "challenger/01_the_impossible_dream.txt": 43,
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
                    # VII.3: arrival frees the link for departures this turn.
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
        diagnostics = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(
            diagnostics,
        ):
            reported_turns = simulation.run()
        trace = output.getvalue()
        turns = self.check_trace(data, trace)
        self.assertEqual(turns, reported_turns)
        self.assertEqual(turns, simulation.turns)
        self.assertEqual(diagnostics.getvalue(), f"Final turns: {turns}\n")
        self.assertTrue(all(drone.finished for drone in simulation.drones))
        return simulation, trace

    def test_all_maps_have_valid_repeatable_output(self) -> None:
        """Check movement correctness separately from optimization targets."""
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
                fresh_data = parse_map_file(filename)
                _, repeated_trace = self.run_checked(
                    fresh_data, fresh_data.find_all_paths(max_paths=5),
                )
                self.assertEqual(trace, repeated_trace)

    def test_all_maps_reach_subject_optima(self) -> None:
        """Measure optimization against the PDF's single reference target."""
        for name, target in TARGETS.items():
            with self.subTest(map=name):
                data = parse_map_file(MAPS / name)
                simulation, _ = self.run_checked(data, data.find_all_paths())
                self.assertEqual(simulation.turns, target)

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

    def test_restricted_link_reused_on_arrival_turn(self) -> None:
        """Two arrivals free capacity for two new departures in that turn."""
        data = self.restricted_map(4, 2)
        simulation, output = self.run_checked(data, data.find_all_paths())
        self.assertEqual(simulation.turns, 4)
        self.assertEqual(output.splitlines()[:2], [
            "D1-start-restricted D2-start-restricted",
            "D1-restricted D2-restricted D3-start-restricted D4-start-restricted",
        ])

    def test_validator_rejects_invalid_restricted_traces(self) -> None:
        """Ensure the checker catches the previous timing/capacity mistakes."""
        data = self.restricted_map(2, 1)
        invalid_traces = [
            # A drone arrives and leaves in one turn.
            "D1-start-restricted\nD1-restricted D1-goal\n",
            # A restricted destination is reached in one turn.
            "D1-restricted\n",
            # Two departures exceed the connection capacity.
            "D1-start-restricted D2-start-restricted\n",
            # D1 waits on a connection instead of arriving next turn.
            "D1-start-restricted\n\n",
        ]
        for trace in invalid_traces:
            with self.subTest(trace=trace), self.assertRaises(AssertionError):
                self.check_trace(data, trace)

    def test_opposing_routes_are_planned_without_deadlock(self) -> None:
        """Future reservations prevent a head-on capacity conflict."""
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
        trial_output = io.StringIO()
        with contextlib.redirect_stdout(trial_output):
            trial_turns = trial._simulate()
        self.assertEqual(trial_turns, 5)
        self.check_trace(data, trial_output.getvalue())
        simulation, _ = self.run_checked(data, paths)
        self.assertEqual(len(simulation.paths), 1)
        self.assertEqual(simulation.turns, 4)

    def test_invalid_candidate_schedule_is_skipped(self) -> None:
        """Route selection retains its fallback for unschedulable candidates."""
        from unittest.mock import patch

        data = parse_map_file(MAPS / "easy/02_simple_fork.txt")
        paths = data.find_all_paths()
        original = Simulator._simulate

        def fail_multiple(simulation, emit_output=True):
            if len(simulation.paths) > 1:
                raise DeadlockError("Unschedulable candidate")
            return original(simulation, emit_output)

        with patch.object(Simulator, "_simulate", fail_multiple):
            simulation, _ = self.run_checked(data, paths)
        self.assertEqual(len(simulation.paths), 1)

    def test_disconnected_map_reports_error_without_traceback(self) -> None:
        """A valid disconnected map produces no movements and exits cleanly."""
        with tempfile.TemporaryDirectory() as folder:
            filename = Path(folder) / "disconnected.txt"
            filename.write_text(
                "nb_drones: 1\nstart_hub: start 0 0\nend_hub: goal 1 0\n",
            )
            data = parse_map_file(filename)
            self.assertEqual(data.find_all_paths(), [])
            result = subprocess.run(
                [sys.executable, str(MAPS.parent / "main.py"), str(filename)],
                capture_output=True, text=True, timeout=10,
            )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            result.stderr, "Error: no route connects start to end.\n",
        )

    def test_future_restricted_arrival_respects_waiting_occupant(self) -> None:
        """A congested exit delays departures without unsafe future arrivals."""
        data = Map()
        data.nb_drones = 5
        start = Zone("start", 0, 0, ZoneMetadata())
        restricted = Zone("restricted", 1, 1, ZoneMetadata("restricted"))
        bottleneck = Zone("bottleneck", 2, 0, ZoneMetadata())
        goal = Zone("goal", 3, 0, ZoneMetadata())
        data.start_hub, data.end_hub = start, goal
        data.zones = [restricted, bottleneck]
        data.zone_by_name = {
            zone.name: zone for zone in (start, restricted, bottleneck, goal)
        }
        data.connections = [
            Connection(start, bottleneck), Connection(start, restricted),
            Connection(restricted, bottleneck), Connection(bottleneck, goal),
        ]
        data.build_neighbors()
        direct = [start, bottleneck, goal]
        via_restricted = [start, restricted, bottleneck, goal]
        simulation = Simulator(data, [direct, via_restricted])
        for drone in simulation.drones:
            drone.path = direct if drone.id <= 3 else via_restricted
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            turns = simulation._simulate()
        self.assertEqual(turns, 6)
        self.check_trace(data, output.getvalue())
        lines = output.getvalue().splitlines()
        self.assertIn("D4-restricted", lines[1])
        self.assertNotIn("D5-start-restricted", lines[1])
        self.assertIn("D5-start-restricted", lines[2])
        self.assertNotIn("D4-", lines[2])  # D4 waits for the bottleneck.


if __name__ == "__main__":
    unittest.main()
