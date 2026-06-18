with open("map.txt", "r") as f:
    lines = f.readlines(20)

for line in lines:
    line = line.strip()

    if not line:
        continue