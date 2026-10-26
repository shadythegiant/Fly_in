from typing import Dict, List, Tuple, Optional, Any
import heapq


class Graph:
    def __init__(self) -> None:
        self.adj_list: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {}
        self.nodes: Dict[str, Dict[str, Any]] = {}

    def add_node(self, name: str, metadata: Dict[str, Any]) -> None:
        if name not in self.adj_list:
            self.adj_list[name] = []
            self.nodes[name] = metadata

    def add_edge(
            self,
            node_a: str,
            node_b: str,
            metadata: Dict[str, Any]
    ) -> None:
        if node_a in self.adj_list and node_b in self.adj_list:
            if any(neighbor == node_b for
                   neighbor, _ in self.adj_list[node_a]):
                raise ValueError("Duplicates connection detected")
            self.adj_list[node_a].append((node_b, metadata))
            self.adj_list[node_b].append((node_a, metadata))
        else:
            raise ValueError(
                f"❌ -> {node_a} {node_b} don't exist in the graph")

    def get_neighbor(self, name: str) -> List[Tuple[str, Dict[str, Any]]]:
        return self.adj_list.get(name, [])


def dijkstra_shortest_path(
    graph: Graph, start: str, end: str
) -> Optional[Tuple[float, List[str]]]:
    """Finds the shortest path accounting """
    # Heap element format: (accumulated_cost, current_node, path_taken)
    priority_queue: List[Tuple[float, str, List[str]]] = [(0, start, [start])]
    distances: Dict[str, float] = {start: 0.0}

    while priority_queue:
        current_cost, current_node, path = heapq.heappop(priority_queue)

        if current_node == end:
            return current_cost, path

        if current_cost > distances.get(current_node, float('inf')):
            continue

        for neighbor, _ in graph.get_neighbor(current_node):
            neighbor_type = graph.nodes[neighbor].get("zone", "normal")

            if neighbor_type == "blocked":
                continue
            if neighbor_type == "restricted":
                cost_weight = 2.0
            elif neighbor_type == "priority":
                cost_weight = 0.9
            else:
                cost_weight = 1.0

            new_cost = current_cost + cost_weight

            if new_cost < distances.get(neighbor, float('inf')):
                distances[neighbor] = new_cost
                heapq.heappush(priority_queue, (new_cost,
                               neighbor, path + [neighbor]))

    return None
