# from parser_1 import parse_map_file


# def main():
#     data = parse_map_file("map.txt")


# if __name__ == "__main__":
#     main()


from parser import parse_map_file
from simulator import Simulator
from visualizer import InteractiveVisualizer


def main():
    data = parse_map_file("map.txt")
    paths = data.find_all_paths(max_paths=5)

    sim = Simulator(data, paths)
    sim.run()

    visualizer = InteractiveVisualizer(data, sim.history)
    visualizer.show()


if __name__ == "__main__":
    main()
