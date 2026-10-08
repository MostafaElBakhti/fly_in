*This project has been created as part of the 42 curriculum by mel-bakh.*

# Fly-in

## Description

A Python drone routing simulator. It moves drones from a start hub to an end hub through connected zones, aiming to reduce turns while respecting movement costs and capacity limits.

## Instructions

Requires **Python 3.10+**. From the project folder:

```sh
python3 -m pip install pygame flake8 mypy
python3 main.py
```

The entry point reads `map.txt`, prints the simulation, and opens the Pygame
replay automatically. To use another map, call `main` with its filename:

```sh
python3 -c 'from main import main; main("maps/easy/01_linear_path.txt")'
```

The Makefile also provides these commands:

```sh
make run          # Run the simulation and open the replay
make debug        # Run main.py with Python's pdb debugger
make clean        # Remove Python and mypy caches
make lint         # Run flake8 and the required mypy checks
make lint-strict  # Run flake8 and strict mypy checks
```

## Algorithm

1. **Parse:** read the map and build a graph of zones and bidirectional connections.
2. **Find routes:** use Dijkstra's algorithm with destination costs: normal and priority = 1 turn, restricted = 2 turns. Blocked zones are excluded; priority zones break equal-cost ties.
3. **Find alternatives:** branch from previously found routes, temporarily excluding connections and earlier nodes to find another route without loops. The current entry point requests up to five routes.
4. **Assign drones:** balance assignments using route cost plus the number of drones already assigned. Trial simulations compare each prefix of the candidate routes (the first route, the first two, and so on), keeping the fastest safe result.
5. **Schedule:** finish restricted arrivals, plan departures, and check zone and connection capacities. Preview the following turn to ensure restricted arrivals have space; delay departures when needed. Report a deadlock if no safe continuation exists.

Routes are calculated before movement and reused. This is a heuristic: it does not guarantee the fewest possible turns. Each Dijkstra search takes `O(V² + E)` with the current linear minimum search. Saved visualizer history uses `O(drones × turns)` memory.

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

## Visualization

`python3 main.py` opens the Pygame replay after the simulation completes.
It draws connections and colored zones at their map coordinates, with zone names
when there is enough space. Unknown color words fall back to gray.

Orange circles show drone positions and move smoothly between the saved turns.
Restricted moves pass through the connection's midpoint. Drones at the same
position overlap. Playback starts automatically at two turns per second.
Resize the window to fit the map, or use these controls:

- **Space:** pause or resume playback.
- **R:** reset to turn zero, keeping the current pause state.
- **Close the window:** exit the replay.

## Example

Save as `example.txt`, then run:

```sh
python3 -c 'from main import main; main("example.txt")'
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
as `Final turns: 3`. Route lists are also printed before the movement lines by
`find_all_paths()`.

## Resources

- [Project subject](new_subject.pdf): full rules and requirements.
- [Princeton: shortest paths](https://algs4.cs.princeton.edu/44sp/): Dijkstra's algorithm.
- [Pygame documentation](https://www.pygame.org/docs/): graphical display and controls.

AI assistance for this README: reading the subject, checking the implementation, drafting documentation, and verifying the example. Add any earlier AI use in the project before submission.
AI assistance was also used to implement and check the Pygame replay and its
command-line integration.
