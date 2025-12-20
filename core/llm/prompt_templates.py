"""Prompt templates for LLM graph generation."""

GRAPH_GENERATION_SYSTEM = """You are a semantic scene graph generator for a 2D game/world design tool.
Given a prompt describing a location or world, generate a graph of interconnected nodes representing
sub-locations, elements, and their spatial relationships.

CRITICAL: You must position nodes SEMANTICALLY based on their real-world spatial meaning:
- Vertical (y): sky/canopy/rooftops at TOP (y=0.8-1.0), ground level in MIDDLE (y=0.3-0.6), underground/basements at BOTTOM (y=-0.5 to 0)
- Horizontal (x): spread nodes realistically - entrances at edges, central plazas in middle, related areas clustered together
- Water features (streams, rivers) should flow horizontally or diagonally
- Bridges should be positioned near water
- Paths should connect logically between areas
- Forest canopy ABOVE clearings, roots/caves BELOW

Position coordinates range from -1.0 to 1.0 for both x and y.

Rules:
- Each node should be a distinct location, landmark, or element
- Edges represent spatial relationships (adjacent_to, connected_to, contains, leads_to, overlooks, inside)
- Consider logical spatial layout (entrances connect to main areas, etc.)
- Include variety: major landmarks, minor details, atmospheric elements
- Node types available: location, landmark, element, character, atmosphere
- Size ranges from 0.5 (minor) to 2.0 (major landmark)

You MUST respond with valid JSON only, no markdown or explanation."""

GRAPH_GENERATION_TEMPLATE = """Create a semantic scene graph for: "{master_prompt}"

{context_section}

Depth Level: {depth_level} (0=world, 1=region, 2=area, 3=building, 4=room)
Generate exactly {max_nodes} nodes with appropriate detail for this depth level.
Higher depth = more granular details.

IMPORTANT: Position each node with realistic x,y coordinates (-1.0 to 1.0):
- Think about where each element would ACTUALLY be in physical space
- Vertical axis (y): +1 is UP (sky, canopy, rooftops), -1 is DOWN (underground, basements)
- Horizontal axis (x): -1 is LEFT/WEST, +1 is RIGHT/EAST
- Central/main areas near (0, 0)
- Entrances and exits at the edges
- Group related elements together spatially

Respond with this exact JSON structure:
{{
  "nodes": [
    {{
      "name": "Node Name",
      "description": "Brief description of this location/element",
      "node_type": "location|landmark|element|character|atmosphere",
      "size": 1.0,
      "is_expandable": true,
      "x": 0.0,
      "y": 0.0
    }}
  ],
  "edges": [
    {{
      "source": "Source Node Name",
      "target": "Target Node Name",
      "relationship": "connected_to|adjacent_to|contains|leads_to|overlooks|inside",
      "label": "optional label"
    }}
  ],
  "summary": "One-sentence summary of the generated scene"
}}"""

GRAPH_MODIFICATION_TEMPLATE = """Current scene graph state:
{current_graph_json}

User instruction: "{instruction}"

Modify the graph according to the instruction. Return the complete updated graph.
You may add, remove, or modify nodes and edges as requested.
Keep existing nodes unless the instruction specifically asks to remove them.
Preserve the x,y positions of existing nodes unless the modification requires moving them.

Respond with this exact JSON structure:
{{
  "nodes": [
    {{
      "name": "Node Name",
      "description": "Brief description",
      "node_type": "location|landmark|element|character|atmosphere",
      "size": 1.0,
      "is_expandable": true,
      "x": 0.0,
      "y": 0.0
    }}
  ],
  "edges": [
    {{
      "source": "Source Node Name",
      "target": "Target Node Name",
      "relationship": "connected_to|adjacent_to|contains|leads_to|overlooks|inside",
      "label": ""
    }}
  ],
  "summary": "Summary of changes made"
}}"""


class PromptTemplates:
    """Manages prompt engineering templates for graph generation."""

    def build_generation_prompt(self, master_prompt: str, context: str = None,
                                 depth_level: int = 0, max_nodes: int = 8) -> str:
        """Build the generation prompt."""
        context_section = ""
        if context:
            context_section = f"Context from parent: {context}\n"

        return GRAPH_GENERATION_TEMPLATE.format(
            master_prompt=master_prompt,
            context_section=context_section,
            depth_level=depth_level,
            max_nodes=max_nodes
        )

    def build_modification_prompt(self, instruction: str, current_graph_json: str) -> str:
        """Build the modification prompt."""
        return GRAPH_MODIFICATION_TEMPLATE.format(
            instruction=instruction,
            current_graph_json=current_graph_json
        )

    @property
    def system_prompt(self) -> str:
        """Get the system prompt."""
        return GRAPH_GENERATION_SYSTEM
