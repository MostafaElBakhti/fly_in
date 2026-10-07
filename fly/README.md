*This project has been created as part of the 42 curriculum by mel-bakh.*

# Fly-in

## Description

A Python drone routing simulator. It moves drones from a start hub to an end hub through connected zones, aiming to reduce turns while respecting movement costs and capacity limits.

## Instructions

Requires **Python 3.10+**. From the project folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 main.py map.txt
```

Omitting the filename uses `map.txt`. To open the Pygame visualizer:

```sh
python3 main.py map.txt --visual
```

## Algorithm

1. **Parse:** read the map and build a graph of zones and bidirectional connections.
2. **Find routes:** use Dijkstra's algorithm with destination costs: normal and priority = 1 turn, restricted = 2 turns. Blocked zones are excluded; priority zones break equal-cost ties.
3. **Find alternatives:** branch from the shortest route, temporarily excluding connections and earlier nodes to find another route without loops. The current entry point requests up to two routes.
4. **Assign drones:** balance assignments using route cost plus the number of drones already assigned. Trial simulations compare using the first route alone against using both routes, keeping the faster result.
5. **Schedule:** finish restricted arrivals, plan departures, and check zone and connection capacities. Preview the following turn to ensure restricted arrivals have space; delay departures when needed. Report a deadlock if no safe continuation exists.

Routes are calculated before movement and reused. This is a heuristic: it does not guarantee the fewest possible turns. Each Dijkstra search takes `O(V² + E)` with the current linear minimum search. Saved visualizer history uses `O(drones × turns)` memory.

## Visualization

Run `python3 main.py map.txt --visual` to open the Pygame replay after the
simulation completes. It shows the network at the map coordinates, zone colors
and types, zone and link capacities, and clearly marked start/end hubs. Unknown
color words receive a consistent fallback color. Blocked zones have an X.

Purple badges show drone positions; drones sharing a position are grouped with
a count. Restricted moves appear midway along a connection during transit.
The turn counter and progress bar make waiting and movement costs easy to follow.
Resize the window to fit the map. Buttons and keyboard controls support replay:

- **Right:** next turn.
- **Left:** previous turn.
- **Space:** play/pause (one turn every 0.7 seconds).
- **R:** reset to turn zero.
- **Esc:** close.

## Example

Save as `example.txt`, then run `python3 main.py example.txt`:

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

Each line is one turn; waiting drones are omitted. Restricted moves use `D1-source-destination` during transit, then `D1-destination` on arrival. The total is printed to stderr as `Final turns: 3`. The current code also prints `tt` and route lists before the movement lines.

## Resources

- [Project subject](new_subject.pdf): full rules and requirements.
- [Python virtual environments](https://docs.python.org/3/tutorial/venv.html): installation setup.
- [Princeton: shortest paths](https://algs4.cs.princeton.edu/44sp/): Dijkstra's algorithm.
- [Pygame documentation](https://www.pygame.org/docs/): graphical display and controls.

AI assistance for this README: reading the subject, checking the implementation, drafting documentation, and verifying the example. Add any earlier AI use in the project before submission.
AI assistance was also used to implement and check the Pygame replay and its
command-line integration.
