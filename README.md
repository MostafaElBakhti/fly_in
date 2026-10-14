<div align="center">

# Fly-in

**A capacity-aware drone routing simulator with an interactive Pygame replay.**

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Pygame](https://img.shields.io/badge/UI-Pygame-2C2D72)
![42 Project](https://img.shields.io/badge/42-Project-000000?logo=42&logoColor=white)

</div>

Fly-in finds efficient routes through a network of zones and schedules every
drone while respecting zone capacity, connection capacity, restricted-zone
delays, and blocked areas. After the simulation, a responsive mission-control
dashboard replays every turn.

## Highlights

- Weighted route discovery using Dijkstra's algorithm.
- Multiple candidate routes with balanced drone assignment.
- Safe turn planning with occupancy and connection-capacity checks.
- Support for normal, priority, restricted, and blocked zones.
- Smooth interactive replay with a timeline, live statistics, and hover details.
- Clear errors for invalid maps and simulations that cannot progress safely.

## Quick start

Fly-in requires **Python 3.10 or newer**. From the project root:

```sh
python3 -m pip install pygame flake8 mypy
python3 main.py
```

The program reads `map.txt`, prints each movement turn to standard output, and
opens the replay automatically. The final state remains visible until the
window is closed.

### Make commands

| Command | Purpose |
| --- | --- |
| `make run` | Run the simulation and open the replay. |
| `make debug` | Run `main.py` with Python's debugger. |
| `make clean` | Remove generated Python and mypy caches. |
| `make lint` | Run Flake8 and the required mypy checks. |
| `make lint-strict` | Run Flake8 and strict mypy checks. |

## Map format

A map begins with the drone count, defines one start hub and one end hub, then
adds intermediate zones and bidirectional connections. Blank lines and text
after `#` are ignored.

```text
nb_drones: 5
start_hub: start 0 0 [color=green]
hub: junction 1 0 [zone=priority color=blue max_drones=2]
hub: tunnel 2 0 [zone=restricted color=orange]
end_hub: goal 3 0 [color=green]
connection: start-junction
connection: junction-tunnel [max_link_capacity=2]
connection: tunnel-goal
```

### Metadata

| Definition | Supported metadata |
| --- | --- |
| Zone | `zone`, `color`, `max_drones` |
| Connection | `max_link_capacity` |

Zone types behave as follows:

| Type | Movement behavior |
| --- | --- |
| `normal` | Costs one turn to enter. |
| `priority` | Costs one turn and wins equal-cost route ties. |
| `restricted` | Costs two turns to enter. |
| `blocked` | Cannot be used in a route. |

## Algorithm

1. **Parse:** validate the input and build a graph of zones and bidirectional
   connections.
2. **Discover routes:** run Dijkstra's algorithm with weighted destination
   costs. Blocked zones are excluded, while priority zones break equal-cost
   ties.
3. **Find alternatives:** branch from previous routes while temporarily
   excluding earlier nodes and connections. Up to five candidates are kept.
4. **Assign drones:** balance drones using route cost plus the number already
   assigned to each route.
5. **Compare schedules:** simulate every prefix of the candidate route list and
   keep the fastest safe result.
6. **Schedule turns:** plan arrivals and departures, enforce capacities, and
   preview the following turn before committing movement.

Routes are computed before movement and reused. This is a heuristic strategy;
it does not guarantee the theoretical minimum number of turns.

## Simulation

`Simulator.run()` validates the routes, selects a route set, assigns drones,
and records their starting positions at turn zero. It then advances until every
drone reaches the end hub.

Each turn is planned on copies of the drones before updating their real state:

1. Finish arrivals from restricted moves started on the previous turn. These
   drones cannot depart again during the same turn.
2. Try departures along each drone's assigned route. Normal and priority zones
   take one turn to enter; restricted zones take two. Blocked zones cannot be used.
3. Track zone occupancy, reservations for restricted destinations, and departures
   over each connection. Intermediate zones respect `max_drones`; start and end
   hubs are exempt from that limit. Departures over a connection share its
   `max_link_capacity` in both directions.
4. Preview the following turn to check that restricted arrivals have space.
   If the preview fails, delay departures, starting with the highest drone ID,
   and retry. The simulator can fall back to the previous turn's safe preview
   or a plan that also counts current occupants of restricted destinations.
5. Commit the safe turn, print its movements, and save drone positions for replay.
   If no safe continuation is found, raise `DeadlockError`.

Waiting drones stay in place and are omitted from the movement line. A restricted
move prints `D1-source-destination` on departure and `D1-destination` on arrival.
The saved position during transit is the connection's midpoint. The total turn
count is returned by `run()` and printed to stderr as `Final turns: N`.

To run only the simulation without opening a window, use the classes directly
(Pygame is not needed for this command):

```sh
python3 - <<'PY'
from parser import Parser
from simulator import Simulator

data = Parser().parse_map_file("map.txt")
paths = data.find_all_paths(max_paths=5)
simulation = Simulator(data, paths)
simulation.run()
PY
```

## Mission replay

`python3 main.py` opens the Pygame replay after the simulation completes.
It presents the route as a responsive mission-control dashboard with zone-type
rings, connection-capacity badges, mission statistics, a turn timeline, and
hover details for each zone. Unknown color words use a neutral fallback color.

Numbered, color-coded drone markers move smoothly between saved turns.
Restricted moves pass through the connection midpoint, and drones sharing a
position fan out so every marker stays visible. Playback starts automatically
at one turn per second.

| Control | Action |
| --- | --- |
| On-screen buttons | Play, pause, step, reset, or change speed. |
| `Space` | Pause or resume playback. |
| `Left` / `Right` | Step backward or forward one recorded turn. |
| `R` | Return to turn zero and pause. |
| `+` / `-` | Increase or decrease playback speed. |
| Mouse hover | Show a zone's type and capacity. |
| Close window | Exit the replay. |

## Project structure

```text
.
├── main.py          Entry point
├── parser.py        Input parsing and validation
├── classes.py       Zone, connection, and drone models
├── map.py           Graph storage and route discovery
├── simulator.py     Assignment and turn scheduling
├── visualizer.py    Pygame mission replay
├── map.txt          Default demonstration map
└── Makefile         Run, debug, and quality commands
```

## Complexity and limitations

- Each Dijkstra search is `O(V² + E)` because the current implementation uses
  a linear minimum search.
- Replay history uses `O(drones × turns)` memory.
- Candidate routes are limited to five by the entry point.
- Route selection is heuristic and may not produce the absolute global optimum.

## Quality checks

Run the same checks used for the final version:

```sh
make lint
```

For the strictest available type analysis:

```sh
make lint-strict
```

## Example

Save the example as `map.txt`, then run:

```sh
python3 main.py
```

```text
nb_drones: 2
start_hub: start 0 0 [color=green]
hub: mid 1 0 [zone=normal color=blue]
end_hub: end 2 0 [color=yellow]
connection: start-mid
connection: mid-end
```

Expected movement lines:

```text
D1-mid
D1-end D2-mid
D2-end
```

Each line is one turn; waiting drones are omitted. The total is printed to stderr
as `Final turns: 3`.

## Resources

- [Princeton: shortest paths](https://algs4.cs.princeton.edu/44sp/):
  Dijkstra's algorithm.
- [Pygame documentation](https://www.pygame.org/docs/): graphical display
  and controls.

## Project note

This project was created by **mel-bakh** as part of the 42 curriculum.

AI assistance was used to review the subject, check the implementation, draft
documentation, verify the example, and implement and validate the Pygame replay
and its command-line integration.
