from typing import Dict, Any
from graph import Graph

# CONSTANTS
ALLOWED_HUB_KEYS = {"zone", "max_drones", "color"}
ALLOWED_CONN_KEYS = {"max_link_capacity"}
ALLOWED_ZONE_TYPES = {"normal", "blocked", "restricted", "priority"}


def parse_metadata(s: str, line_number: int, context: str) -> Dict[str, Any]:
    """Extracts and validates key-value pairs from brackets based on context"""
    """ ('hub' or 'connection')."""
    metadata: Dict[str, Any] = {}
    start_i = s.find('[')
    end_i = s.find(']')

    # 1. No brackets present
    if start_i == -1 and end_i == -1:
        return {}

    # 2. Mismatched, backward, or trailing text after brackets
    if (start_i == -1 or end_i == -1 or start_i > end_i
            or s[end_i + 1:].strip()):
        raise ValueError(
            f"❌ -> Line {line_number}: Invalid metadata bracket syntax.")

    meta_str = s[start_i + 1:end_i]
    tokens = meta_str.split()

    # 3. Reject empty brackets like [] or [   ]
    if not tokens:
        raise ValueError(
            f"❌ -> Line {line_number}: Empty metadata brackets '[]' "
            "are not allowed.")

    for token in tokens:
        if '=' not in token:
            raise ValueError(
                f"❌ -> Line {line_number}: Invalid key-value pair "
                f"'{token}' (missing '=')."
            )

        key, value = token.split('=', 1)
        if not key or not value:
            raise ValueError(
                f"❌ -> Line {line_number}: Missing key or value in '{token}'."
            )

        if key in metadata:
            raise ValueError(
                f"❌ -> Line {line_number}: Duplicate metadata key '{key}'."
            )

        # 4. Context-specific key whitelist check
        if context == "hub" and key not in ALLOWED_HUB_KEYS:
            raise ValueError(
                f"❌ -> Line {line_number}: Invalid hub metadata key '{key}'."
            )
        if context == "connection" and key not in ALLOWED_CONN_KEYS:
            raise ValueError(
                f"❌ -> Line {line_number}: Invalid connection metadata key "
                f"'{key}'."
            )

        # 5. Value validation (Notice the flat if / elif / elif alignment!)
        if key == "zone":
            if value not in ALLOWED_ZONE_TYPES:
                raise ValueError(
                    f"❌ -> Line {line_number}: Invalid zone type '{value}'."
                )
            metadata[key] = value

        elif key in ("max_drones", "max_link_capacity"):
            try:
                num = int(value)
            except ValueError:
                raise ValueError(
                    f"❌ -> Line {line_number}: '{key}' must be an integer, "
                    f"got '{value}'."
                )
            if num <= 0:
                raise ValueError(
                    f"❌ -> Line {line_number}: '{key}' must be > 0, got {num}."
                )
            metadata[key] = num

        elif key == "color":
            if not value.isalpha():
                raise ValueError(
                    f"❌ -> Line {line_number}: Invalid color '{value}' "
                    "(must be alphabetic)."
                )
            metadata[key] = value

    return metadata


class Parser:
    """Reads a Fly-In map file and populates the Graph object."""

    def __init__(self, filepath: str, graph: Graph) -> None:
        self.filepath = filepath
        self.graph = graph
        self.nb_drones = 0
        self.start_hub_found = False
        self.end_hub_found = False

    def parse(self) -> None:
        """The main execution loop for reading the file line-by-line."""
        with open(self.filepath, 'r') as file:
            for line_number, raw_line in enumerate(file, start=1):
                line = raw_line.split('#')[0].strip()

                # Ignore empty lines and comments
                if not line or line.startswith('#'):
                    continue

                if ':' not in line:
                    raise ValueError(
                        f"❌ -> Line {line_number}: Missing colon separator.")

                prefix, data = line.split(':', 1)
                prefix = prefix.strip()
                data = data.strip()

                if prefix == "nb_drones":
                    self._parse_drones(data, line_number)
                elif prefix == "hub":
                    self._parse_hub(data, line_number, "normal")
                elif prefix == "start_hub":
                    if self.start_hub_found:
                        raise ValueError(
                            f"❌ -> Line {line_number}: "
                            "Duplicate start_hub found.")
                    self.start_hub_found = True
                    self._parse_hub(data, line_number, "start_hub")
                elif prefix == "end_hub":
                    if self.end_hub_found:
                        raise ValueError(
                            f"❌ -> Line {line_number}: "
                            "Duplicate end_hub found.")
                    self.end_hub_found = True
                    self._parse_hub(data, line_number, "end_hub")
                elif prefix == "connection":
                    self._parse_connection(data, line_number)
                else:
                    raise ValueError(
                        f"❌ -> Line {line_number}: Unknown prefix '{prefix}'.")

        # Post-parsing validation to ensure map is solvable
        if not self.start_hub_found or not self.end_hub_found:
            raise ValueError(
                "❌ -> Map is invalid: "
                "Must contain exactly one start_hub and one end_hub.")
        if self.nb_drones <= 0:
            raise ValueError(
                "❌ -> Map is invalid: nb_drones must be a positive integer.")

    def _parse_drones(self, data: str, line_number: int) -> None:
        """Extracts the global number of drones."""
        if self.nb_drones > 0:
            raise ValueError(
                f"❌ -> line {line_number} duplicate nb_drones")
        try:
            self.nb_drones = int(data)
            if self.nb_drones <= 0:
                raise ValueError
        except ValueError:
            raise ValueError(
                f"❌ -> Line {line_number}: "
                "nb_drones must be a positive integer.")

    def _parse_hub(self, data: str, line_number: int, hub_type: str) -> None:
        """Extracts zone coordinates and metadata."""
        metadata = parse_metadata(data, line_number, context="hub")

        bracket_idx = data.find('[')
        if bracket_idx != -1:
            trimmed_data = data[:bracket_idx].strip()
        else:
            trimmed_data = data.strip()

        try:
            name, x_str, y_str = trimmed_data.split()
        except ValueError:
            raise ValueError(
                f"❌ -> Line {line_number}: Invalid hub format. "
                "Expected '<name> <x> <y>'.")

        if '-' in name:
            raise ValueError(
                f"❌ ->  Line {line_number}: "
                f"Zone name '{name}' cannot contain dashes.")

        try:
            metadata["x"] = int(x_str)
            metadata["y"] = int(y_str)
        except ValueError:
            raise ValueError(
                f"❌ -> Line {line_number}: ."
                "Coordinates must be valid integers")

        # Default assignment if the brackets didn't explicitly override
        # the zone type
        if "zone" not in metadata:
            metadata["zone"] = hub_type
        # checking if zone name alreay exists in nodes
        if name in self.graph.nodes:
            raise ValueError(
                f"❌ -> Line {line_number} : duplicate zone")

        self.graph.add_node(name, metadata)

    def _parse_connection(self, data: str, line_number: int) -> None:
        """Extracts connection edges and link capacities."""
        metadata = parse_metadata(data, line_number, context="connection")

        bracket_idx = data.find('[')
        if bracket_idx != -1:
            trimmed_data = data[:bracket_idx].strip()
        else:
            trimmed_data = data.strip()

        try:
            zone_a, zone_b = trimmed_data.split('-')
            zone_a = zone_a.strip()
            zone_b = zone_b.strip()
        except ValueError:
            raise ValueError(
                f"❌ -> Line {line_number}: Invalid connection format."
                "Expected 'zoneA-zoneB'")

        try:
            self.graph.add_edge(zone_a, zone_b, metadata)
        except Exception as e:
            raise ValueError(f"❌ -> Line {line_number}: {e}")
