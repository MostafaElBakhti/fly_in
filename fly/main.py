import sys

from parser import Parser
from simulator import Simulator
from visualizer import Visualizer


def main() -> int:
    """Run map.txt and open the recorded graphical replay."""
    data = Parser().parse_map_file("map.txt")

    paths = data.find_all_paths(max_paths=5)

    simulation = Simulator(
        data,
        paths
    )

    simulation.run()

    # visualizer = Visualizer(data, simulation)
    # visualizer.run()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"Error: {error}")
        sys.exit(1)
