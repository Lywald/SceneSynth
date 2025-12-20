"""Base class for LLM providers."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class GraphGenerationRequest:
    """Request model for graph generation."""
    master_prompt: str
    context: Optional[str] = None
    parent_node_info: Optional[Dict[str, Any]] = None
    depth_level: int = 0
    max_nodes: int = 10


@dataclass
class GraphGenerationResponse:
    """Structured response from LLM."""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    summary: str


@dataclass
class GraphModificationRequest:
    """Request for natural language graph modification."""
    instruction: str
    current_graph_json: str


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._is_configured = False

    @abstractmethod
    def generate_graph(self, request: GraphGenerationRequest) -> GraphGenerationResponse:
        """Generate a new scene graph from a prompt."""
        pass

    @abstractmethod
    def modify_graph(self, request: GraphModificationRequest) -> GraphGenerationResponse:
        """Modify existing graph based on natural language instruction."""
        pass

    @abstractmethod
    def validate_api_key(self) -> bool:
        """Validate the API key is working."""
        pass

    @property
    def is_configured(self) -> bool:
        return self._is_configured
