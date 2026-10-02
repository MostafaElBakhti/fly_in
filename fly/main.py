"""Run the drone simulation for a supplied map file."""
import argparse
import os
import sys
from parser import parse_map_file
from simulator import DeadlockError, Simulator


def main(filename: str = "map.txt", visual: bool = False) -> int:
    """Print movement turns, reporting unsolvable inputs on stderr."""
    data = parse_map_file(filename)
    paths = data.find_all_paths(max_paths=5)

    if not paths:
        print("Error: no route connects start to end.", file=sys.stderr)
        return 1
    try:
        simulation = Simulator(data, paths)
        simulation.run()
        if visual:
            os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
            from visualizer import InteractiveVisualizer
            InteractiveVisualizer(data, simulation.history).show()
    except ImportError:
        print("Install Pygame: python3 -m pip install pygame", file=sys.stderr)
        return 1
    except (DeadlockError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("map_file", nargs="?", default="map.txt")
    arguments.add_argument(
        "--visual", action="store_true", help="show turns in a Pygame window",
    )
    args = arguments.parse_args()
    sys.exit(main(args.map_file, args.visual))
