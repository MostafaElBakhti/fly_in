"""Run the drone simulation for a supplied map file."""

import argparse

from simulator import Simulator
from parser import Parser
from visualizer import Visualizer


def main(filename: str = "map.txt", visual: bool = False) -> int:
    """Run a map and optionally open the recorded graphical replay."""
    data = Parser().parse_map_file(filename)

    paths = data.find_all_paths(max_paths=5)

    simulation = Simulator(
        data,
        paths
    )

    simulation.run()

    visualizer = Visualizer(data, simulation) 
    visualizer.run()


if __name__ == "__main__":
    main()
