"""SceneEdge dataclass for semantic scene graph edges."""
from dataclasses import dataclass, field, asdict
from typing import Dict, Any
from uuid import uuid4
import json


@dataclass
class SceneEdge:
    """
    Represents a spatial relationship between two nodes in the scene graph.

    Edges connect nodes and describe their spatial or logical relationships
    (e.g., adjacent_to, contains, leads_to).
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    source_id: str = ""
    target_id: str = ""

    # Relationship type
    relationship: str = "connected_to"
    label: str = ""

    # Directional properties
    is_bidirectional: bool = True
    weight: float = 1.0  # For path-finding or layout

    # Visual properties
    color: str = "#888888"
    style: str = "solid"  # solid, dashed, dotted
    thickness: float = 2.0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON export."""
        return asdict(self)

    def to_json(self, pretty: bool = True) -> str:
        """Serialize to JSON string."""
        if pretty:
            return json.dumps(self.to_dict(), indent=2)
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SceneEdge':
        """Deserialize from dictionary."""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'SceneEdge':
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def connects(self, node_id: str) -> bool:
        """Check if this edge connects to the given node."""
        return self.source_id == node_id or self.target_id == node_id

    def get_other_node(self, node_id: str) -> str:
        """Get the other node connected by this edge."""
        if self.source_id == node_id:
            return self.target_id
        elif self.target_id == node_id:
            return self.source_id
        raise ValueError(f"Node {node_id} is not connected by this edge")

    def __repr__(self) -> str:
        return f"SceneEdge('{self.source_id[:8]}...' --[{self.relationship}]--> '{self.target_id[:8]}...')"
