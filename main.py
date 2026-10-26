import sys
from graph import Graph, dijkstra_shortest_path
from parser import Parser
from drone import Drone
from scheduler import Scheduler


def main() -> None:
    # 1. Handle Command Line Arguments
    args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    visual_mode = "--visual" in sys.argv
    capacity_mode = "--capacity-info" in sys.argv

    if len(args) != 1:
        print(
            "Usage: python3 main.py <map_file.txt> [--visual]",
            file=sys.stderr,
        )
        sys.exit(1)

    filepath = sys.argv[1]

    # 2. Initialize Core Systems
    graph = Graph()
    # and change the import above to 'from map_parser import Parser'
    map_parser = Parser(filepath, graph)

    # 3. Parse the Map (with strict error catching)
    try:
        map_parser.parse()
    except (ValueError, OSError, UnicodeDecodeError) as e:
        # If we  feed a bad map, it crashes cleanly here!
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # 4. Locate the Start and End Hubs
    start_node = None
    end_node = None
    for name, metadata in graph.nodes.items():
        if metadata.get("zone") == "start_hub":
            start_node = name
        elif metadata.get("zone") == "end_hub":
            end_node = name

    # Safety check just in case
    if not start_node or not end_node:
        print("Error: Map is missing a start_hub or end_hub.")
        sys.exit(1)

    # 5. Calculate the Optimal Route (Dijkstra)
    route_data = dijkstra_shortest_path(graph, start_node, end_node)

    if not route_data:
        print(
            f"❌ -> Error: No valid path exists between '{start_node}' and "
            f"'{end_node}'."
        )
        sys.exit(1)

    _, best_path = route_data

    # 6. Create Drones and Assign Flight Plans
    drones = []
    for i in range(1, map_parser.nb_drones + 1):
        drone = Drone(i, start_node)
        # best_path includes the start node (e.g., ['hub', 'roof1', 'goal'])
        # We slice [1:] so the drone's first instruction is the *next* step.
        drone.path = best_path[1:].copy()
        drones.append(drone)

    # 7. Start Air Traffic Control
    scheduler = Scheduler(graph, drones, start_node, end_node, capacity_mode)
    scheduler.run_simulation()
    print(f"\n--- Simulation Complete in {scheduler.turn_number} Turns ---")
    if visual_mode:
        from visualizer import Visualizer
        vis = Visualizer(graph, scheduler.history)
        vis.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user.", file=sys.stderr)
        sys.exit(0)
