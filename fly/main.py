"""Run the drone simulation for a supplied map file."""

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
    return (0)


if __name__ == "__main__":
    main()
