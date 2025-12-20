"""Gemini API provider for graph generation."""
import json
from typing import Dict, Any, List

from .base_provider import (
    BaseLLMProvider, GraphGenerationRequest, GraphGenerationResponse,
    GraphModificationRequest
)
from .prompt_templates import PromptTemplates

from config import DEFAULT_MODEL


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API implementation."""

    def __init__(self, api_key: str, model_name: str = None):
        super().__init__(api_key)
        self.model_name = model_name or DEFAULT_MODEL
        self.templates = PromptTemplates()
        self._client = None

    def _get_client(self):
        """Lazy initialization of the Gemini client."""
        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
                self._is_configured = True
            except ImportError:
                raise ImportError(
                    "google-genai package not installed. "
                    "Install with: pip install google-genai"
                )
        return self._client

    def generate_graph(self, request: GraphGenerationRequest) -> GraphGenerationResponse:
        """Generate a scene graph from a prompt."""
        client = self._get_client()

        # Build context if parent info provided
        context = None
        if request.parent_node_info:
            context = f"Parent node: {request.parent_node_info.get('name', 'Unknown')} - {request.parent_node_info.get('description', '')}"

        # Build the prompt
        prompt = self.templates.build_generation_prompt(
            master_prompt=request.master_prompt,
            context=context or request.context,
            depth_level=request.depth_level,
            max_nodes=request.max_nodes
        )

        # Call the API
        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=[
                    {"role": "user", "parts": [{"text": self.templates.system_prompt}]},
                    {"role": "model", "parts": [{"text": "I understand. I will generate semantic scene graphs in JSON format."}]},
                    {"role": "user", "parts": [{"text": prompt}]}
                ],
                config={
                    "response_mime_type": "application/json",
                }
            )

            # Parse the response
            response_text = response.text
            data = json.loads(response_text)

            return GraphGenerationResponse(
                nodes=data.get("nodes", []),
                edges=data.get("edges", []),
                summary=data.get("summary", "")
            )

        except json.JSONDecodeError as e:
            # Try to extract JSON from the response
            response_text = response.text
            try:
                # Find JSON in response
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start >= 0 and end > start:
                    data = json.loads(response_text[start:end])
                    return GraphGenerationResponse(
                        nodes=data.get("nodes", []),
                        edges=data.get("edges", []),
                        summary=data.get("summary", "")
                    )
            except:
                pass
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")

        except Exception as e:
            raise RuntimeError(f"LLM API call failed: {e}")

    def modify_graph(self, request: GraphModificationRequest) -> GraphGenerationResponse:
        """Modify an existing graph based on natural language instruction."""
        client = self._get_client()

        # Build the prompt
        prompt = self.templates.build_modification_prompt(
            instruction=request.instruction,
            current_graph_json=request.current_graph_json
        )

        # Call the API
        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=[
                    {"role": "user", "parts": [{"text": self.templates.system_prompt}]},
                    {"role": "model", "parts": [{"text": "I understand. I will modify scene graphs based on instructions."}]},
                    {"role": "user", "parts": [{"text": prompt}]}
                ],
                config={
                    "response_mime_type": "application/json",
                }
            )

            # Parse the response
            response_text = response.text
            data = json.loads(response_text)

            return GraphGenerationResponse(
                nodes=data.get("nodes", []),
                edges=data.get("edges", []),
                summary=data.get("summary", "")
            )

        except json.JSONDecodeError as e:
            # Try to extract JSON from the response
            response_text = response.text
            try:
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start >= 0 and end > start:
                    data = json.loads(response_text[start:end])
                    return GraphGenerationResponse(
                        nodes=data.get("nodes", []),
                        edges=data.get("edges", []),
                        summary=data.get("summary", "")
                    )
            except:
                pass
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")

        except Exception as e:
            raise RuntimeError(f"LLM API call failed: {e}")

    def validate_api_key(self) -> bool:
        """Validate the API key by making a simple request."""
        try:
            client = self._get_client()
            # Make a simple request to validate
            response = client.models.generate_content(
                model=self.model_name,
                contents="Say 'hello' in one word."
            )
            return True
        except Exception:
            return False


class MockGeminiProvider(BaseLLMProvider):
    """Mock provider for testing without API."""

    # Semantic positions for common location types
    SEMANTIC_POSITIONS = {
        # Sky/canopy level (y ~ 0.8)
        "Forest Canopy": (0.0, 0.9),
        "Watchtower": (0.7, 0.7),
        "Castle": (0.0, 0.6),
        "Rooftop": (0.3, 0.8),
        "Sky Bridge": (0.0, 0.75),

        # Upper ground level (y ~ 0.3-0.5)
        "Temple": (0.5, 0.4),
        "Main Gate": (-0.8, 0.3),
        "Market Square": (0.0, 0.2),
        "Central Plaza": (0.0, 0.0),
        "Tavern": (-0.4, 0.1),
        "Garden": (0.6, 0.3),
        "Stable": (-0.6, 0.0),
        "Fountain": (0.0, 0.15),

        # Ground level (y ~ 0.0 to -0.3)
        "Forest Path": (-0.3, -0.2),
        "River Bridge": (0.4, -0.1),
        "Stream": (0.5, -0.2),
        "Clearing": (0.2, -0.1),
        "Crossroads": (0.0, -0.3),

        # Below ground (y ~ -0.5 to -0.9)
        "Underground Passage": (0.0, -0.6),
        "Cellar": (-0.3, -0.5),
        "Dungeon": (0.0, -0.8),
        "Cave Entrance": (0.5, -0.4),
        "Root System": (0.0, -0.7),
    }

    def __init__(self, api_key: str = "mock"):
        super().__init__(api_key)
        self._is_configured = True

    def _get_semantic_position(self, name: str) -> tuple:
        """Get semantic position based on name, or generate plausible one."""
        import random

        # Check for exact match
        if name in self.SEMANTIC_POSITIONS:
            return self.SEMANTIC_POSITIONS[name]

        # Check for partial matches
        name_lower = name.lower()
        for key, pos in self.SEMANTIC_POSITIONS.items():
            if key.lower() in name_lower or any(word in name_lower for word in key.lower().split()):
                # Add some variation
                return (pos[0] + random.uniform(-0.15, 0.15),
                        pos[1] + random.uniform(-0.1, 0.1))

        # Semantic inference based on keywords
        if any(word in name_lower for word in ["sky", "canopy", "tower", "roof", "top", "high"]):
            return (random.uniform(-0.5, 0.5), random.uniform(0.6, 0.9))
        elif any(word in name_lower for word in ["underground", "cave", "dungeon", "cellar", "below", "root"]):
            return (random.uniform(-0.5, 0.5), random.uniform(-0.8, -0.4))
        elif any(word in name_lower for word in ["river", "stream", "water", "bridge", "pond"]):
            return (random.uniform(0.2, 0.7), random.uniform(-0.3, 0.1))
        elif any(word in name_lower for word in ["gate", "entrance", "door", "exit"]):
            return (random.uniform(-0.9, -0.5), random.uniform(-0.2, 0.3))
        elif any(word in name_lower for word in ["center", "central", "plaza", "square"]):
            return (random.uniform(-0.2, 0.2), random.uniform(-0.1, 0.2))

        # Default: random ground-level position
        return (random.uniform(-0.7, 0.7), random.uniform(-0.3, 0.4))

    def generate_graph(self, request: GraphGenerationRequest) -> GraphGenerationResponse:
        """Generate a mock scene graph with semantic positioning."""
        import random

        node_names = [
            "Central Plaza", "Main Gate", "Market Square", "Temple",
            "Tavern", "Castle", "Forest Path", "River Bridge",
            "Watchtower", "Underground Passage", "Garden", "Stable"
        ]

        # Select random nodes
        selected = random.sample(node_names, min(request.max_nodes, len(node_names)))

        nodes = []
        for name in selected:
            x, y = self._get_semantic_position(name)
            nodes.append({
                "name": name,
                "description": f"A {name.lower()} in the scene",
                "node_type": random.choice(["location", "landmark", "element"]),
                "size": round(random.uniform(0.7, 1.5), 1),
                "is_expandable": True,
                "x": round(x, 2),
                "y": round(y, 2)
            })

        # Create edges
        edges = []
        for i in range(len(selected) - 1):
            edges.append({
                "source": selected[i],
                "target": selected[i + 1],
                "relationship": random.choice(["connected_to", "adjacent_to", "leads_to"]),
                "label": ""
            })

        # Add a few random cross-connections
        for _ in range(min(3, len(selected) // 2)):
            src = random.choice(selected)
            tgt = random.choice(selected)
            if src != tgt:
                edges.append({
                    "source": src,
                    "target": tgt,
                    "relationship": "connected_to",
                    "label": ""
                })

        return GraphGenerationResponse(
            nodes=nodes,
            edges=edges,
            summary=f"Generated {len(nodes)} nodes based on: {request.master_prompt[:50]}..."
        )

    def modify_graph(self, request: GraphModificationRequest) -> GraphGenerationResponse:
        """Mock modification - just return the current graph."""
        data = json.loads(request.current_graph_json)
        return GraphGenerationResponse(
            nodes=[n for n in data.get("nodes", [])],
            edges=[e for e in data.get("edges", [])],
            summary=f"Modified based on: {request.instruction[:50]}..."
        )

    def validate_api_key(self) -> bool:
        """Always valid for mock."""
        return True
