# Current-code audit against new_subject.pdf (version 2.0)

Each map was run through the public main.py CLI in three fresh processes. This audit does not modify solver files. Raw stdout, stderr diagnostics, and movement-only logs are saved beside this report.

Benchmarks are from subject VII.6 (printed pages 16–17), not the outdated thresholds in test_simulator.py or maps/README.md. Missing an optimum is an optimization result, not a correctness failure.

| Map | Turns | Subject optimum | Within +25% | Movement replay | Raw stdout | Repeatable* |
|---|---:|---:|---|---|---|---|
| [challenger/01_the_impossible_dream.txt](challenger__01_the_impossible_dream.stdout.txt) | 43 | 43 | Yes | Pass | Pass | Yes |
| [easy/01_linear_path.txt](easy__01_linear_path.stdout.txt) | 4 | 4 | Yes | Pass | Pass | Yes |
| [easy/02_simple_fork.txt](easy__02_simple_fork.stdout.txt) | 4 | 4 | Yes | Pass | Pass | Yes |
| [easy/03_basic_capacity.txt](easy__03_basic_capacity.stdout.txt) | 4 | 4 | Yes | Pass | Pass | Yes |
| [hard/01_maze_nightmare.txt](hard__01_maze_nightmare.stdout.txt) | 13 | 13 | Yes | Pass | Pass | Yes |
| [hard/02_capacity_hell.txt](hard__02_capacity_hell.stdout.txt) | 16 | 16 | Yes | Pass | Pass | Yes |
| [hard/03_ultimate_challenge.txt](hard__03_ultimate_challenge.stdout.txt) | 26 | 26 | Yes | Pass | Pass | Yes |
| [medium/01_dead_end_trap.txt](medium__01_dead_end_trap.stdout.txt) | 8 | 8 | Yes | Pass | Pass | Yes |
| [medium/02_circular_loop.txt](medium__02_circular_loop.stdout.txt) | 10 | 10 | Yes | Pass | Pass | Yes |
| [medium/03_priority_puzzle.txt](medium__03_priority_puzzle.stdout.txt) | 6 | 6 | Yes | Pass | Pass | Yes |

*Exact stdout equality in three runs is a sample check, not proof of determinism.

## Findings

- All movement-only logs are independently replayed: valid adjacent edges, blocked zones excluded, one action per drone per turn, immediate arrival on the next turn after restricted travel, shared undirected link capacity, simultaneous end-of-turn zone capacity, and delivery of every drone.
- stdout is checked for movement lines only; stderr must contain exactly the matching final-turn summary. See each map's .stderr.txt file.
- The independent replay follows current VII.3: an arrival frees its restricted link for another departure in the same turn.
- The simulator plans each turn on copied drones and previews the next turn before committing. This permits restricted pipelining while checking mandatory arrival capacity. Unsafe departures or head-on conflicts are retried with more waiting; a checked conservative preview is retained as fallback.
- Token ordering is deterministic by drone ID; the audit compares stdout, stderr, and exit codes across three fresh processes per map.
- Full change details and before/after comparisons are in ../CHANGES_AND_RESULTS.md.

## Scope

This audit validates the supplied maps, not all possible graphs or global optimality. The subject's published optimum is the benchmark. Full submission compliance additionally requires type/lint checks, Makefile, root README, and visual simulation feedback.
