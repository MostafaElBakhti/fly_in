"""Audit current map outputs against new_subject.pdf without changing the solver.

Run: python3 audit_maps.py
Results, raw stdout, and extracted movement traces go into audit_results/.
"""
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from parser import parse_map_file

ROOT = Path(__file__).resolve().parent
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
MOVE = re.compile(r"D[1-9]\d*-[^-\s]+(?:-[^-\s]+)?")


def validate(data, lines):
    """Independently replay simultaneous output under subject VII.2/VII.3.

    Arrival frees a restricted link for departures in the SAME turn. Only the
    final zone occupancy is checked, allowing a vacated zone to be reused.
    A transit tuple represents a drone on a link, not occupying either zone.
    """
    start, end = data.start_hub.name, data.end_hub.name
    positions = {f"D{i}": start for i in range(1, data.nb_drones + 1)}
    capacities = {
        frozenset((c.zone_a.name, c.zone_b.name)): c.max_link_capacity
        for c in data.connections
    }
    errors = []
    for turn, line in enumerate(lines, 1):
        try:
            if all(p == end for p in positions.values()):
                raise ValueError("movement output after all drones arrived")
            if line != line.strip() or "  " in line:
                raise ValueError("invalid whitespace")
            actions = {}
            for token in line.split():
                if not MOVE.fullmatch(token):
                    raise ValueError(f"invalid movement token {token}")
                drone, *action = token.split("-")
                if drone not in positions or drone in actions:
                    raise ValueError(f"unknown or duplicate drone {drone}")
                actions[drone] = action
            following = dict(positions)
            links = Counter()
            entrants = Counter()
            for drone, position in positions.items():
                action = actions.get(drone)
                if isinstance(position, tuple):
                    if action != [position[1]]:
                        raise ValueError(f"{drone} must arrive after one transit turn")
                    following[drone] = position[1]
                    entrants[position[1]] += 1
                    # VII.3: the arriving drone frees the link this turn.
                    continue
                if action is None:
                    continue
                if position == end:
                    raise ValueError(f"delivered drone {drone} moved")
                destination = action[-1]
                if destination not in data.zone_by_name:
                    raise ValueError(f"undefined destination {destination}")
                edge = frozenset((position, destination))
                if edge not in capacities:
                    raise ValueError(f"missing connection {position}-{destination}")
                kind = data.zone_by_name[destination].metadata.zone
                if kind == "blocked":
                    raise ValueError(f"{drone} entered blocked zone")
                if len(action) == 2:
                    if action[0] != position or kind != "restricted":
                        raise ValueError(f"invalid in-flight movement for {drone}")
                    following[drone] = (position, destination)
                else:
                    if kind == "restricted":
                        raise ValueError(f"{drone} reached restricted zone in one turn")
                    following[drone] = destination
                    entrants[destination] += 1
                links[edge] += 1
            for edge, count in links.items():
                if count > capacities[edge]:
                    raise ValueError(f"connection {sorted(edge)} over capacity")
            occupancy = Counter(p for p in following.values() if isinstance(p, str))
            for name in occupancy.keys() | entrants.keys():
                if name in (start, end):
                    continue
                capacity = data.zone_by_name[name].metadata.max_drones
                if occupancy[name] > capacity or entrants[name] > capacity:
                    raise ValueError(f"zone {name} over capacity")
            positions = following
        except ValueError as error:
            errors.append(f"turn {turn}: {error}")
            break
    if not errors and not all(p == end for p in positions.values()):
        errors.append("output ended before all drones arrived")
    return errors


def run_map(filename):
    # Exercise main() itself, selecting its input without changing map.txt.
    code = (
        "import sys, main\n"
        "from parser import parse_map_file\n"
        "main.parse_map_file = lambda _: parse_map_file(sys.argv[1])\n"
        "main.main()\n"
    )
    return subprocess.run(
        [sys.executable, "-c", code, str(filename)], cwd=ROOT,
        capture_output=True, text=True, timeout=30,
    )


def main():
    folder = ROOT / "audit_results"
    folder.mkdir(exist_ok=True)
    results = []
    filenames = sorted((ROOT / "maps").rglob("*.txt"))
    if {str(f.relative_to(ROOT / "maps")) for f in filenames} != set(TARGETS):
        raise ValueError("map collection differs from subject benchmark table")
    for filename in filenames:
        name = str(filename.relative_to(ROOT / "maps"))
        run = run_map(filename)
        lines, extra = [], []
        for number, line in enumerate(run.stdout.splitlines(), 1):
            if line and all(MOVE.fullmatch(token) for token in line.split()):
                lines.append(line)
            else:
                extra.append({"line": number, "text": line})
        errors = validate(parse_map_file(filename), lines)
        if run.returncode or run.stderr:
            errors.append(f"exit={run.returncode}; stderr={run.stderr.strip()}")
        repeated = [run_map(filename) for _ in range(2)]
        repeatable = all(r.stdout == run.stdout and r.returncode == run.returncode for r in repeated)
        stem = name.replace("/", "__").removesuffix(".txt")
        (folder / f"{stem}.stdout.txt").write_text(run.stdout)
        (folder / f"{stem}.moves.txt").write_text("\n".join(lines) + "\n")
        result = {
            "map": name, "turns": len(lines), "optimum": TARGETS[name],
            "within_25_percent": len(lines) <= TARGETS[name] * 1.25,
            "movement_valid": not errors, "errors": errors,
            "stdout_format_valid": not extra and not errors,
            "extra_stdout": extra, "repeatable_in_3_processes": repeatable,
        }
        results.append(result)
        print(f"{name}: {len(lines)}/{TARGETS[name]} turns; movement={'PASS' if not errors else 'FAIL'}; stdout={'PASS' if result['stdout_format_valid'] else 'FAIL'}; repeatable={repeatable}")
    (folder / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    report = [
        "# Current-code audit against new_subject.pdf (version 2.0)", "",
        "Production Python files were not changed. Each map was run through main() in three fresh processes, overriding only its input filename. Raw stdout and extracted movement-only logs are saved beside this report.", "",
        "Benchmarks are from subject VII.6 (printed pages 16–17), not the outdated thresholds in test_simulator.py or maps/README.md. Missing an optimum is an optimization result, not a correctness failure.", "",
        "| Map | Turns | Subject optimum | Within +25% | Movement replay | Raw stdout | Repeatable* |",
        "|---|---:|---:|---|---|---|---|",
    ]
    for r in results:
        yes = lambda value: "Yes" if value else "No"
        report.append(f"| {r['map']} | {r['turns']} | {r['optimum']} | {yes(r['within_25_percent'])} | {'Pass' if r['movement_valid'] else 'Fail'} | {'Pass' if r['stdout_format_valid'] else 'Fail'} | {yes(r['repeatable_in_3_processes'])} |")
    report += ["", "*Exact stdout equality in three runs is a sample check, not proof of determinism.", "",
        "## Findings", "",
        "- All movement-only logs are independently replayed: valid adjacent edges, blocked zones excluded, one action per drone per turn, immediate arrival on the next turn after restricted travel, shared undirected link capacity, simultaneous end-of-turn zone capacity, and delivery of every drone.",
        "- Every raw stdout log includes a path-list debug line from map.py and a `Final turns:` summary from simulator.py. These are not movement lines and do not conform to VII.5; they are excluded only for the independent replay, retained in raw logs.",
        "- VII.3 explicitly frees a restricted link on the arrival turn. The simulator copies connection_transit into link_usage before processing arrivals and does not decrement link_usage on arrival. This adds waiting and explains a missed optimization opportunity, without making the supplied movement traces illegal.",
        "- The simulator reserves restricted destination capacity during transit. The subject describes availability after departures, so this conservative reservation can prevent pipelining even when next-turn arrival would be feasible.",
        "- Existing unittest run: five test methods, 13 failing cases. Most fail on the extra `Final turns:` stdout line. After that is removed, tests also expect simulator.history snapshots, but the current simulator never records any. Restricted-link tests enforce the older rule (arrival still consumes link capacity), contradicting the current PDF.",
        "- Restricted arrivals iterate an unordered set of Drone objects. Output token order can vary between fresh processes; compare the repeatability column. Order does not invalidate a simultaneous movement line.",
        "- main.py always selects map.txt; passing a map filename on the command line currently does not select it. The audit overrides its parser input to exercise every supplied map without overwriting map.txt.",
        "- Confirmed unsolvable-map defect: a valid disconnected map containing only start and end causes `find_all_paths()` to raise `TypeError: 'NoneType' object is not iterable`, because the debug print iterates first_path before checking for None. This violates VII.4 graceful unsolvable-map handling.",
        "- A two-drone route through a restricted zone of capacity 2 and a capacity-1 incoming link takes 5 turns in the current simulator. The subject permits a valid 4-turn trace: start D1; arrive D1/start D2; finish D1/arrive D2; finish D2. This isolates the unnecessarily retained arrival-turn link usage.",
        "- flake8 and mypy are not installed in this environment, so their mandatory checks were not run. No root Makefile or root README.md was present. main.py has its visualizer import and calls commented out; simulator.history is empty, and its terminal movement output is uncolored. The website currently visualizes pathfinding rather than moving drones, so required visual simulation feedback is not established.",
        "", "## Scope", "",
        "This audit validates the supplied maps, not all possible graphs or mathematical global optimality. The subject's published optimum is the benchmark. Full submission compliance additionally requires type/lint checks, Makefile, root README, graceful unsolvable-map handling, and visual simulation feedback.",
    ]
    (folder / "REPORT.md").write_text("\n".join(report) + "\n")


if __name__ == "__main__":
    main()
