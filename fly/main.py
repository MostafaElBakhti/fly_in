"""Run the drone simulation for a supplied map file."""
import argparse
import os
import sys
from parser import parse_map_file
from simulator import DeadlockError, Simulator


def main(filename: str = "map.txt", visual: bool = False) -> int:
    """Print movement turns, reporting unsolvable inputs on stderr."""
    # try:
    data = parse_map_file(filename)
    paths = data.find_all_paths(max_paths=5)
    simulation = Simulator(data, paths)
    simulation.run()
    # except Exception as e:
    #     print(e)



if __name__ == "__main__":
    main()
