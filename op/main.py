from parser_1 import parse_map_file
from map import Map

def main():
    data = parse_map_file("map.txt")
    paths = data.find_all_paths(5)
    # test = find_all_paths(data, 5)
    # for path in paths :
    #     print(f"best route : {"-".join(x.name for x in path)}")



if __name__ == "__main__":
    main()
