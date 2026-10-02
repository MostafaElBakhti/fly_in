"""Audit current map outputs against new_subject.pdf without changing the solver.

Run: python3 audit_maps.py
Results, raw stdout, and extracted movement traces go into audit_results/.
"""
import json
import argparse
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
    # Exercise the public CLI without changing map.txt.
    return subprocess.run(
        [sys.executable, str(ROOT / "main.py"), str(filename)], cwd=ROOT,
        capture_output=True, text=True, timeout=30,
    )


def main(output_dir="audit_results"):
    folder = ROOT / output_dir
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
        if run.returncode:
            errors.append(f"exit={run.returncode}; stderr={run.stderr.strip()}")
        summary_valid = run.stderr == f"Final turns: {len(lines)}\n"
        if not summary_valid:
            errors.append(f"unexpected diagnostic output: {run.stderr!r}")
        repeated = [run_map(filename) for _ in range(2)]
        repeatable = all(
            (r.stdout, r.stderr, r.returncode)
            == (run.stdout, run.stderr, run.returncode) for r in repeated
        )
        stem = name.replace("/", "__").removesuffix(".txt")
        (folder / f"{stem}.stdout.txt").write_text(run.stdout)
        (folder / f"{stem}.stderr.txt").write_text(run.stderr)
        (folder / f"{stem}.moves.txt").write_text("\n".join(lines) + "\n")
        result = {
            "map": name, "turns": len(lines), "optimum": TARGETS[name],
            "within_25_percent": len(lines) <= TARGETS[name] * 1.25,
            "movement_valid": not errors, "errors": errors,
            "stdout_format_valid": not extra and not errors,
            "extra_stdout": extra, "repeatable_in_3_processes": repeatable,
            "stderr_summary_valid": summary_valid,
        }
        results.append(result)
        print(f"{name}: {len(lines)}/{TARGETS[name]} turns; movement={'PASS' if not errors else 'FAIL'}; stdout={'PASS' if result['stdout_format_valid'] else 'FAIL'}; repeatable={repeatable}")
    (folder / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    report = [
        "# Current-code audit against new_subject.pdf (version 2.0)", "",
        "Each map was run through the public main.py CLI in three fresh processes. This audit does not modify solver files. Raw stdout, stderr diagnostics, and movement-only logs are saved beside this report.", "",
        "Benchmarks are from subject VII.6 (printed pages 16–17), not the outdated thresholds in test_simulator.py or maps/README.md. Missing an optimum is an optimization result, not a correctness failure.", "",
        "| Map | Turns | Subject optimum | Within +25% | Movement replay | Raw stdout | Repeatable* |",
        "|---|---:|---:|---|---|---|---|",
    ]
    for r in results:
        yes = lambda value: "Yes" if value else "No"
        stem = r['map'].replace('/', '__').removesuffix('.txt')
        report.append(f"| [{r['map']}]({stem}.stdout.txt) | {r['turns']} | {r['optimum']} | {yes(r['within_25_percent'])} | {'Pass' if r['movement_valid'] else 'Fail'} | {'Pass' if r['stdout_format_valid'] else 'Fail'} | {yes(r['repeatable_in_3_processes'])} |")
    report += ["", "*Exact stdout equality in three runs is a sample check, not proof of determinism.", "",
        "## Findings", "",
        "- All movement-only logs are independently replayed: valid adjacent edges, blocked zones excluded, one action per drone per turn, immediate arrival on the next turn after restricted travel, shared undirected link capacity, simultaneous end-of-turn zone capacity, and delivery of every drone.",
        "- stdout is checked for movement lines only; stderr must contain exactly the matching final-turn summary. See each map's .stderr.txt file.",
        "- The independent replay follows current VII.3: an arrival frees its restricted link for another departure in the same turn.",
        "- The simulator plans each turn on copied drones and previews the next turn before committing. This permits restricted pipelining while checking mandatory arrival capacity. Unsafe departures or head-on conflicts are retried with more waiting; a checked conservative preview is retained as fallback.",
        "- Token ordering is deterministic by drone ID; the audit compares stdout, stderr, and exit codes across three fresh processes per map.",
        "- Full change details and before/after comparisons are in ../CHANGES_AND_RESULTS.md.",
        "", "## Scope", "",
        "This audit validates the supplied maps, not all possible graphs or global optimality. The subject's published optimum is the benchmark. Full submission compliance additionally requires type/lint checks, Makefile, root README, and visual simulation feedback.",
    ]
    (folder / "REPORT.md").write_text("\n".join(report) + "\n")


if __name__ == "__main__":
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("--output-dir", default="audit_results")
    main(arguments.parse_args().output_dir)
