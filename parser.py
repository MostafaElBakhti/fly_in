with open("map.txt", "r") as f:
    lines = f.readlines()

    if not lines :
            print("nothing to print")

for line in lines:
    line = line.strip()

    print(line)