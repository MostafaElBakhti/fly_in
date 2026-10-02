# Current-code audit against new_subject.pdf (version 2.0)

Production Python files were not changed. Each map was run through main() in three fresh processes, overriding only its input filename. Raw stdout and extracted movement-only logs are saved beside this report.

Benchmarks are from subject VII.6 (printed pages 16–17), not the outdated thresholds in test_simulator.py or maps/README.md. Missing an optimum is an optimization result, not a correctness failure.

| Map | Turns | Subject optimum | Within +25% | Movement replay | Raw stdout | Repeatable* |
|---|---:|---:|---|---|---|---|
| [challenger/01_the_impossible_dream.txt](challenger__01_the_impossible_dream.stdout.txt) | 43 | 43 | Yes | Pass | Fail | No |
| [easy/01_linear_path.txt](easy__01_linear_path.stdout.txt) | 4 | 4 | Yes | Pass | Fail | Yes |
| [easy/02_simple_fork.txt](easy__02_simple_fork.stdout.txt) | 4 | 4 | Yes | Pass | Fail | Yes |
| [easy/03_basic_capacity.txt](easy__03_basic_capacity.stdout.txt) | 4 | 4 | Yes | Pass | Fail | Yes |
| [hard/01_maze_nightmare.txt](hard__01_maze_nightmare.stdout.txt) | 13 | 13 | Yes | Pass | Fail | Yes |
| [hard/02_capacity_hell.txt](hard__02_capacity_hell.stdout.txt) | 16 | 16 | Yes | Pass | Fail | Yes |
| [hard/03_ultimate_challenge.txt](hard__03_ultimate_challenge.stdout.txt) | 26 | 26 | Yes | Pass | Fail | Yes |
| [medium/01_dead_end_trap.txt](medium__01_dead_end_trap.stdout.txt) | 8 | 8 | Yes | Pass | Fail | Yes |
| [medium/02_circular_loop.txt](medium__02_circular_loop.stdout.txt) | 15 | 10 | No | Pass | Fail | Yes |
| [medium/03_priority_puzzle.txt](medium__03_priority_puzzle.stdout.txt) | 7 | 6 | Yes | Pass | Fail | Yes |

*Exact stdout equality in three runs is a sample check, not proof of determinism.

## Findings

- All movement-only logs are independently replayed: valid adjacent edges, blocked zones excluded, one action per drone per turn, immediate arrival on the next turn after restricted travel, shared undirected link capacity, simultaneous end-of-turn zone capacity, and delivery of every drone.
- Every raw stdout log includes a path-list debug line from map.py and a `Final turns:` summary from simulator.py. These are not movement lines and do not conform to VII.5; they are excluded only for the independent replay, retained in raw logs.
- VII.3 explicitly frees a restricted link on the arrival turn. The simulator copies connection_transit into link_usage before processing arrivals and does not decrement link_usage on arrival. This adds waiting and explains a missed optimization opportunity, without making the supplied movement traces illegal.
- The simulator reserves restricted destination capacity during transit. The subject describes availability after departures, so this conservative reservation can prevent pipelining even when next-turn arrival would be feasible.
- Existing unittest run: five test methods, 13 failing cases. Most fail on the extra `Final turns:` stdout line. After that is removed, tests also expect simulator.history snapshots, but the current simulator never records any. Restricted-link tests enforce the older rule (arrival still consumes link capacity), contradicting the current PDF.
- Restricted arrivals iterate an unordered set of Drone objects. Output token order can vary between fresh processes; compare the repeatability column. Order does not invalidate a simultaneous movement line.
- main.py always selects map.txt; passing a map filename on the command line currently does not select it. The audit overrides its parser input to exercise every supplied map without overwriting map.txt.

- Confirmed disconnected-map defect: a valid map with only start and end raises `TypeError: 'NoneType' object is not iterable` in `find_all_paths()`, violating VII.4. The debug print iterates the missing path before the None check.
- A two-drone route through a restricted zone of capacity 2 and incoming link capacity 1 takes 5 turns in the current simulator. The subject permits a valid 4-turn schedule by starting D2 on D1's arrival turn.
- flake8 and mypy are unavailable, so mandatory lint/type checks were not run. The root Makefile and README.md are absent. main.py disables the visualizer, simulator.history is empty, and movement output is uncolored; required visual simulation feedback is not established.

## Valid faster schedules

The two `.reference.moves.txt` logs were constructed independently of the solver, and passed the same replay checker. They demonstrate the subject targets are attainable on the actual supplied maps:

- [Circular loop: 10 turns](medium__02_circular_loop.reference.moves.txt), compared with the solver's 15.
- [Priority puzzle: 6 turns](medium__03_priority_puzzle.reference.moves.txt), compared with the solver's 7.

The checker itself passed three unit tests, covering allowed same-turn link reuse and rejecting premature/late restricted arrival, duplicate/unknown drones, nonadjacent moves, over-capacity links/zones, blocked zones, and incomplete delivery. Run `python3 -m unittest test_audit_maps -v`.

## Scope

This audit validates the supplied maps, not all possible graphs or mathematical global optimality. The subject's published optimum is the benchmark. Full submission compliance additionally requires type/lint checks, Makefile, root README, graceful unsolvable-map handling, and visual simulation feedback.
