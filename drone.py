from typing import List, Optional


class Drone:
    """Represents a single pilot in the Fly-In simulation."""

    def __init__(self, drone_id: int, start_node: str) -> None:
        # 1. Identity
        self.id: int = drone_id

        # 2. Spatial State
        self.current_location: str = start_node
        self.path: List[str] = []  # The flight plan assigned by the Scheduler

        # 3. Temporal/Transit State (The "Limbo" Tracker)
        self.transit_target: Optional[str] = None
        self.turns_until_arrival: int = 0

        # 4. Lifecycle State
        self.is_delivered: bool = False
        self.delivery_turn: int = 0

    def __str__(self) -> str:
        """Returns a human-readable state of the drone for debugging."""
        if self.is_delivered:
            status = "Delivered"
        elif self.transit_target:
            status = (
                f"Mid-air to {self.transit_target} "
                f"({self.turns_until_arrival} turns left)"
            )
        else:
            status = f"Waiting at {self.current_location}"

        return f"[Drone {self.id}] {status}"
