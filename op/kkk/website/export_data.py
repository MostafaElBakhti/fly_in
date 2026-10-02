"""Refresh the website's read-only snapshot of the Python project."""
import json
import sys
import math
import io
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from parser import parse_map_file
from classes import Zone, Connection


def serialize(value):
    if isinstance(value, Zone):
        return value.name
    if isinstance(value, Connection):
        return f"{value.zone_a.name}-{value.zone_b.name}"
    if isinstance(value, dict):
        return {str(serialize(k)): serialize(v) for k, v in value.items()}
    if isinstance(value, set):
        return sorted((serialize(v) for v in value), key=str)
    if isinstance(value, (list, tuple)):
        return [serialize(v) for v in value]
    if isinstance(value, float) and math.isinf(value):
        return "∞"
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return type(value).__name__


def trace_algorithm(data, algorithm):
    """Record actual Python locals before each executed line (no drone movement)."""
    events = []
    filename = str(ROOT / "map.py")

    def tracer(frame, event, arg):
        if frame.f_code.co_filename != filename:
            return None
        if frame.f_code.co_name not in {"dijkstra", "find_all_paths"}:
            return None
        if event in {"line", "return"}:
            frames = []
            current = frame
            while current is not None:
                if current.f_code.co_filename == filename and current.f_code.co_name in {"dijkstra", "find_all_paths"}:
                    frames.append({
                        "function": current.f_code.co_name,
                        "locals": {k: serialize(v) for k, v in current.f_locals.items() if k != "self"},
                    })
                current = current.f_back
            snapshot = {"line": frame.f_lineno, "event": event, "frames": frames}
            if event == "return":
                snapshot["result"] = serialize(arg)
            events.append(snapshot)
        return tracer

    original = sys.gettrace()
    try:
        sys.settrace(tracer)
        with redirect_stdout(io.StringIO()):
            result = data.dijkstra() if algorithm == "dijkstra" else data.find_all_paths(max_paths=5)
    finally:
        sys.settrace(original)
    return {"events": events, "result": serialize(result)}


def export():
    data = parse_map_file(str(ROOT / "map.txt"))
    snapshot = {
        "nb_drones": data.nb_drones,
        "start": data.start_hub.name,
        "end": data.end_hub.name,
        "zones": [
            {"name": z.name, "x": z.x, "y": z.y,
             "type": z.metadata.zone, "capacity": z.metadata.max_drones,
             "color": z.metadata.color}
            for z in data.zone_by_name.values()
        ],
        "connections": [
            {"a": c.zone_a.name, "b": c.zone_b.name,
             "capacity": c.max_link_capacity}
            for c in data.connections
        ],
        "sources": {
            name: (ROOT / name).read_text()
            for name in ("main.py", "parser.py", "classes.py", "map.py", "simulator.py", "visualizer.py")
        },
        "traces": {name: trace_algorithm(data, name) for name in ("dijkstra", "paths")},
    }
    target = Path(__file__).with_name("data.js")
    target.write_text("window.PROJECT = " + json.dumps(snapshot, ensure_ascii=True) + ";\n")
    print(f"Updated {target}")


if __name__ == "__main__":
    export()
