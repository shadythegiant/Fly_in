
# Fly-In: Autonomous Drone Routing & Air Traffic Control Simulation

*This project has been created as part of the 42 curriculum by `azahidi`.*

## Description

**Fly-In** is a turn-based multi-agent pathfinding and air traffic control simulation written in Python 3.10+. The objective of the project is to route a fleet of autonomous drones from a single `start_hub` to an `end_hub` across a weighted, capacity-constrained graph in the minimum number of simulation turns.

The simulation models real-world air traffic constraints:

- **Zone Types & Turn Costs:**

  - `normal`: Standard hub requiring 1 turn to enter.
  - `priority`: Preferred routing hub requiring 1 turn to enter, prioritized during pathfinding.
  - `restricted`: High-security zone requiring 2 turns to traverse (Turn 1 in-flight on the connection link, Turn 2 landing in the zone).
  - `blocked`: Inaccessible zone that drones must route around.
- **Capacity Constraints:**
  - Every intermediate hub enforces a `max_drones` occupancy limit (default: `1`), while `start_hub` and `end_hub` hold unlimited drones.
  - Every connection edge enforces a `max_link_capacity` limit (default: `1`), restricting how many drones can traverse the connection simultaneously.

---

## Instructions

### Prerequisites & Installation

Ensure you have **Python 3.10+** installed. Install the required dependencies (`pygame`, `flake8`, `mypy`) using the `Makefile`:

```bash
make install


### Running the Simulation

* **Run the default map in terminal mode:**
```bash
make run

```

- **Run a specific map via CLI:**

```bash
python3 main.py maps/easy/01_linear_path.txt

```

- **Run with the interactive Pygame visualizer:**

```bash
python3 main.py maps/medium/01_dead_end_trap.txt --visual

```

- **Makefile shortcuts for individual maps (Terminal & Visual):**

```bash
make run_easy-01
make run_medium-01
make run_hard-01
make run_challenger-01

make visual_easy-01
make visual_challenger-01

```

### Linting & Static Type Checking

To verify PEP 8 compliance (`flake8`) and static type safety (`mypy`):

```bash
make lint
make lint-strict

```

---

## Algorithm Choices & Implementation Strategy

### 1. Graph Representation & Strict Map Parsing (`graph.py`, `parser.py`)

The network is represented using a custom adjacency-list `Graph` class (`adj_list` and `nodes` dictionaries) without external graph libraries. The `Parser` validates map syntax line-by-line, stripping comments, verifying coordinate pairs, enforcing positive integer capacities, rejecting duplicate zones/connections, and ensuring both `start_hub` and `end_hub` exist.

### 2. Initial Weighted Dijkstra Pathfinding (`dijkstra_shortest_path`)

To find the optimal initial route from `start_hub` to `end_hub`, we use **Dijkstra's shortest-path algorithm** backed by a binary min-heap (`heapq`):

- `blocked` zones are filtered out completely.
- `restricted` zones are assigned a weight of `2.0` to reflect their 2-turn transit cost.
- `normal` zones are assigned a weight of `1.0`.
- `priority` zones are assigned a weight of `0.9`. Giving `priority` zones a slight discount (`0.9` vs `1.0`) ensures Dijkstra naturally prefers priority corridors over equal-length normal paths without distorting multi-hop turn calculations or creating zero-cost cycles.

### 3. Turn-Based Air Traffic Control & Reactive Detours (`scheduler.py`)

Because all drones start with the globally shortest path, bottlenecks naturally form at capacity-1 hubs and restricted corridors. Rather than pre-computing an exponentially large Space-Time A* reservation table, `Scheduler` combines **three-phase turn execution** with **bounded reactive detours** (`_find_open_detour`):

1. **Phase 1 — Process Mid-Air Arrivals:** Drones currently mid-air toward a `restricted` zone (`turns_until_arrival > 0`) decrement their arrival timer, release the connection link capacity (`connection_occupancy[conn_key] -= 1`), land in their target hub, and are locked in `has_moved_this_turn` so they cannot move twice in a single tick.
2. **Phase 2 — Dynamic Congestion Avoidance:** Available grounded drones inspect their next planned hub (`drone.path[0]`). If the next hub or link is at capacity (`_can_enter == False`), the scheduler runs a bounded Dijkstra search (`_find_open_detour`) from the drone's current location. This search requires the immediate first step to be currently open and only accepts alternative routes within a strict cost tolerance (`remaining_cost + 2.0`), dynamically splitting traffic across parallel forks while avoiding dead-end traps.
3. **Phase 3 & 4 — Capacity Reservation & Output:** When a drone moves, it immediately decrements occupancy in its origin zone and reserves capacity in its destination zone (preventing mid-air race conditions when multiple drones target the same restricted hub). Movements are sorted by drone ID and printed in the exact `D<ID>-<zone>` or `D<ID>-<connection>` format.

---

## Visual Representation Features

Launching the simulation with `--visual` opens a hardware-accelerated **Pygame** replay visualizer (`visualizer.py`) built from turn snapshots recorded by the scheduler:

- **Auto-Scaled Topological Layout:** Arbitrary map coordinates `(x, y)` are normalized to fit the window with responsive resizing and fullscreen support.
- **Role & Metadata Color Coding:** Zones are rendered using their map-defined `color` metadata (or semantic defaults: green for `start_hub`, red for `end_hub`, orange for `restricted`, gold for `priority`), with capacity badges (`max_drones`) displayed beneath each node.
- **Smooth Frame Interpolation & Orbital Offsets:** Drones animate smoothly between zones across turns. When multiple drones occupy the same hub (`start_hub`, `end_hub`, or multi-drone hubs), they arrange themselves in a circular orbit around the node center so every `D<ID>` label remains legible.
- **2-Turn Restricted Transit Highlighting:** Drones in transit toward a `restricted` zone are highlighted with an orange tint and white border on Turn 1 before turning solid gold upon landing on Turn 2.
- **Interactive Playback Controls:**

- `SPACE` / `Right Arrow`: Step forward one turn
- `Left Arrow`: Step backward one turn
- `A`: Toggle automatic playback
- `R`: Reset simulation to Turn 0
- `F`: Toggle Fullscreen

---

## Example Input and Expected Output

### Example Map (`maps/easy/01_linear_path.txt`)

```text
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal

```

### Execution & Expected Output

```bash
$ python3 main.py maps/easy/01_linear_path.txt
D1-waypoint1
D1-waypoint2 D2-waypoint1
D1-goal D2-waypoint2
D2-goal

```

---

## Resources

### Classic References

- **Dijkstra's Algorithm:** E. W. Dijkstra, *"A note on two problems in connexion with graphs"*, Numerische Mathematik, 1959.
- **Python `heapq` Priority Queue Documentation:** [https://docs.python.org/3/library/heapq.html](https://docs.python.org/3/library/heapq.html)
- **Python `typing` & Mypy Static Type Checking:** [https://mypy.readthedocs.io/](https://mypy.readthedocs.io/)
- **Pygame Documentation:** [https://www.pygame.org/docs/](https://www.pygame.org/docs/)

### AI Usage

In accordance with the subject's AI guidelines, AI assistance was used as a learning and review partner for the following tasks:

- **Algorithmic Discussion & Edge-Case Analysis:** Discussing multi-agent bottleneck scenarios, priority-zone weighting trade-offs (`0.9` vs `1.0`), and capacity reservation invariants during 2-turn restricted zone transits.
- **Pygame Visualizer Math:** Assisting with coordinate normalization and circular orbital trigonometry (`math.cos` / `math.sin`) to prevent overlapping drone sprites on high-capacity hubs.
- **Code Auditing & Type Safety:** Reviewing `flake8` formatting and `mypy --strict` type annotations across modules, as well as structuring this `README.md` documentation.
