# Pathfinding and scheduling fixes — changes and new results

The changes below were checked against `new_subject.pdf`, version 2.0,
particularly movement rules VII.2/VII.3, output format VII.5, and the benchmark
table in VII.6 (printed pages 16–17).

## What changed

### Clean output and graceful errors

- `map.py`: the path debug print was already removed when implementation began.
  Its existing `first_path is None` guard is preserved. No debug path list is
  printed, and an unreachable path returns `[]`.
- `main.py`: detects an empty path result, prints
  `Error: no route connects start to end.` on stderr, and exits with status 1.
  Scheduling errors are reported without a Python traceback.
- `simulator.py`: `Final turns: N` now goes to stderr. Stdout contains only
  movement lines. `run()` returns the turn count and stores it in `self.turns`.
- `main.py` accepts a map filename. With no argument it still uses `map.txt`.

### Safe simultaneous scheduling and restricted-link reuse

The old simulator counted both current zone occupants and future restricted
arrivals against capacity immediately. It also kept a restricted link busy for
its arrival turn. Together these rules unnecessarily delayed following drones.

The first fix used a full timetable search. At the user's request, the current
implementation restores the old, clearer turn-by-turn structure. There is no
heap, time/index search, or complete route timetable.

1. Keep the existing path assignment loops and candidate-route prefix comparison.
2. `_plan_turn()` runs the old two-phase movement loop on shallow copies of the
   drones, so the real state stays unchanged while decisions are being checked.
3. Phase 1 finishes restricted arrivals. Their links are immediately reusable.
4. Phase 2 starts new moves, repeating when a departure frees capacity. Each drone
   can move only once. Zone occupancy, reservations, and link usage are simple
   per-turn counters, matching the old simulator's variables.
5. A restricted departure may target a currently occupied zone, because its
   arrival occurs next turn. The number of new reservations is still bounded by
   the destination's capacity.
6. `_simulate()` previews the following turn using conservative reservations.
   A turn is accepted only if its mandatory arrivals fit after departures and it
   permits progress. The checked preview is saved as a safe fallback.
7. If a proposed turn would cause an unsafe arrival or a head-on deadlock, keep
   the highest-ID eligible drone waiting and retry. Lower-ID drones get priority.
8. Commit the accepted states together and print tokens in ascending drone ID
   order. Arriving drones cannot move again during that turn.

Only the current and next turns are checked; the entire simulation is not planned
in advance. Previewing happens on copied drones, retaining the original Zone and
Connection objects. No external graph library is used. A no-progress turn raises
DeadlockError, allowing route selection to try a different candidate set.

### Tests and audit

- `test_simulator.py` uses the current PDF's exact targets.
- Movement correctness and optimization targets are separate test methods.
- The movement checker allows same-turn reuse of an arriving restricted link.
- Assertions use the replayed movement-line count, the return value of `run()`,
  and `self.turns`; they no longer require the empty `history` list.
- Regression cases cover restricted timing, link reuse, future destination
  congestion, opposing routes, route-selection fallback, and disconnected maps.
- `audit_maps.py` runs the actual CLI, independently replays movements, validates
  the stderr turn summary, and compares stdout/stderr/exit codes in three fresh
  processes per map. It supports a separate output directory to preserve the
  original audit.
- The website's Python source/trace snapshot was regenerated, and its outdated
  explanation about the removed debug print was corrected.

## New results

All ten maps now match the published optimum. Every output passed independent
movement replay and movement-only stdout validation. All ten also produced
identical stdout, stderr, and exit codes in three fresh processes each.

| Map | Before | After | Subject optimum | Movement / stdout |
|---|---:|---:|---:|---|
| Linear path | 4 | 4 | 4 | Pass / Pass |
| Simple fork | 4 | 4 | 4 | Pass / Pass |
| Basic capacity | 4 | 4 | 4 | Pass / Pass |
| Dead end trap | 8 | 8 | 8 | Pass / Pass |
| Circular loop | 15 | **10** | 10 | Pass / Pass |
| Priority puzzle | 7 | **6** | 6 | Pass / Pass |
| Maze nightmare | 13 | 13 | 13 | Pass / Pass |
| Capacity hell | 16 | 16 | 16 | Pass / Pass |
| Ultimate challenge | 26 | 26 | 26 | Pass / Pass |
| Impossible dream | 43 | 43 | 43 | Pass / Pass |

The original raw outputs included debug/summary lines on stdout. The new outputs
contain only movement lines; summaries are saved separately as stderr logs.

The disconnected-map regression exits with status 1, empty stdout, and one clear
error line on stderr. The two-turn arrival tests also confirm that arrival and a
second move by the same drone cannot happen in one turn.

## Verification and saved outputs

Run the full suite:

```sh
python3 -m unittest discover -s . -p 'test_*.py' -v
```

Result: **12 test methods passed**, including per-map subtests.

Reproduce the independent three-process audit:

```sh
python3 audit_maps.py --output-dir audit_results_after
```

- [New per-map report and output links](audit_results_after/REPORT.md)
- [New machine-readable results](audit_results_after/results.json)
- [Original audit for comparison](audit_results/REPORT.md)

## How to run a map

```sh
python3 main.py maps/medium/02_circular_loop.txt
```

To keep movements and diagnostics separate:

```sh
python3 main.py maps/medium/02_circular_loop.txt > moves.txt 2> summary.txt
```

## Remaining scope

Matching these ten targets does not prove global optimality on arbitrary maps.
Route generation still uses at most five candidates, route-set selection considers
prefixes, and scheduling is a greedy turn loop with one-turn lookahead and drone-ID
priority. These choices can miss better schedules on other graphs.

This change does not establish complete submission compliance: mandatory
flake8/mypy tools are unavailable here, and root Makefile/README requirements and
visual drone-simulation feedback still need separate work. `history` remains
empty; this change does not activate the old matplotlib visualizer.
