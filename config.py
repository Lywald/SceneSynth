"""SceneSynth configuration constants."""

APP_NAME = "SceneSynth AI"
APP_VERSION = "0.1.0"

# Default LLM settings
DEFAULT_MODEL = "gemini-2.0-flash"
DEFAULT_NODE_COUNT = 8
MAX_NODE_COUNT = 20
MIN_NODE_COUNT = 3

# Node types
NODE_TYPES = [
    "location",
    "landmark",
    "element",
    "character",
    "atmosphere"
]

# Node colors by type
NODE_COLORS = {
    "location": "#4A90D9",
    "landmark": "#E67E22",
    "element": "#27AE60",
    "character": "#9B59B6",
    "atmosphere": "#95A5A6"
}

# Edge relationship types
EDGE_RELATIONSHIPS = [
    "connected_to",
    "adjacent_to",
    "contains",
    "leads_to",
    "overlooks",
    "inside"
]

# Graph layout settings
LAYOUT_SCALE = 400
LAYOUT_ITERATIONS = 50
NODE_BASE_RADIUS = 40
