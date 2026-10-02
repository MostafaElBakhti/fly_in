"""Run the drone simulation for a supplied map file."""
import argparse
import sys
from parser import parse_map_file
from simulator import DeadlockError, Simulator


def main(filename: str = "map.txt") -> int:
    """Print movement turns, reporting unsolvable inputs on stderr."""
    data = parse_map_file(filename)
    paths = data.find_all_paths(max_paths=5)

    if not paths:
        print("Error: no route connects start to end.", file=sys.stderr)
        return 1
    try:
        Simulator(data, paths).run()
    except (DeadlockError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("map_file", nargs="?", default="map.txt")
    sys.exit(main(arguments.parse_args().map_file))
