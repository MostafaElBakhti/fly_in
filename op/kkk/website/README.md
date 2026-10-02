# Fly-in website

A dependency-free website showing the actual graph from `map.txt`, variables,
explanatory steps for `dijkstra` and `find_all_paths`, and the project's Python
source. Run simulation plays a recorded execution of your actual Python code.
Use Step, Back, Reset, the timeline, and playback speed to inspect each line.
Variables show the state before the highlighted line executes. When Dijkstra is
called inside find_all_paths, both function scopes are displayed. Drone movement
is not simulated.

Open `website/index.html` directly in your browser (no server required), or run
from `/home/mostafa/Desktop/fly_in/tt`:

```sh
python3 -m http.server 8000 --bind 127.0.0.1 --directory /home/mostafa/Desktop/fly_in/tt/website
```

Then visit http://localhost:8000.

After editing Python files or `map.txt`, refresh the bundled snapshot:

```sh
python3 website/export_data.py
```

The exporter uses your parser and records Dijkstra and find_all_paths with
Python's tracing mechanism. It never runs drone simulation. Refresh the snapshot
after changing the map or Python code; playback uses this bundled snapshot.
If port 8000 is occupied, substitute 8001 in the command and browser URL.
