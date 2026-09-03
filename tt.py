self.zones = [
    Zone("A", 1, 0, metadata_A),
    Zone("B", 1, 1, metadata_B),
    Zone("C", 2, 1, metadata_C)
]

self.connections = [
    Connection(START, A),
    Connection(START, B),
    Connection(A, END),
    Connection(B, C),
    Connection(C, END)
]   

self.zone_by_name = {
    "A": Zone("A", 1, 0, metadata),
    "B": Zone("B", 1, 1, metadata),
    "C": Zone("C", 2, 1, metadata)
}

# // **********************************************
distances = {
    START: 0,
    END:   ∞,
    A:     ∞,
    B:     ∞,
    C:     ∞
}

unvisited = {
    START,
    END,
    A,
    B,
    C
}

current = START because (0, 1)

# // **********************************************

unvisited.remove(START)
unvisited = {A, B, C, END}

START.neighbors = {
    A: connection_START_A,
    B: connection_START_B
}
