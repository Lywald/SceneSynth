"""Image generation using Google GenAI SDK with Vertex AI."""
import base64
from typing import Optional


class SceneImageGenerator:
    """
    Generates scene images from semantic graphs using Google GenAI SDK with Vertex AI.
    """

    IMAGE_MODEL = "gemini-2.5-flash-image"  # Model with image generation support

    def __init__(self, api_key: str = None, project_id: str = None, location: str = "us-central1"):
        self.api_key = api_key
        self.project_id = project_id
        self.location = location
        self._client = None

    def _get_client(self):
        """Get or create the GenAI client."""
        if self._client is None:
            try:
                from google import genai

                if self.project_id:
                    # Use Vertex AI backend
                    self._client = genai.Client(
                        vertexai=True,
                        project=self.project_id,
                        location=self.location
                    )
                elif self.api_key:
                    # Use API key backend
                    self._client = genai.Client(api_key=self.api_key)
                else:
                    raise ValueError("Either project_id (for Vertex AI) or api_key is required.")

            except ImportError:
                raise ImportError(
                    "google-genai package not installed. "
                    "Install with: pip install google-genai"
                )
        return self._client

    def generate_scene_image(
        self,
        graph_json: str,
        graph_screenshot: bytes,
        scene_name: str = "scene",
        style: str = "top-down 2D game art"
    ) -> Optional[bytes]:
        """
        Generate a scene image from the graph data and screenshot.

        Args:
            graph_json: JSON representation of the scene graph
            graph_screenshot: PNG bytes of the graph visualization
            scene_name: Name of the scene for the prompt
            style: Art style for the generated image

        Returns:
            PNG image bytes or None if generation failed
        """
        client = self._get_client()

        # Build the prompt
        prompt = self._build_image_prompt(graph_json, scene_name, style)

        try:
            # Encode screenshot as base64
            screenshot_b64 = base64.b64encode(graph_screenshot).decode('utf-8')

            # Call with image generation config
            response = client.models.generate_content(
                model=self.IMAGE_MODEL,
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": "image/png",
                                    "data": screenshot_b64
                                }
                            }
                        ]
                    }
                ],
                config={
                    "response_modalities": ["IMAGE", "TEXT"],
                    "temperature": 0.8,
                }
            )

            # Extract generated image from response
            if response.candidates:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        image_data = part.inline_data.data
                        if isinstance(image_data, str):
                            return base64.b64decode(image_data)
                        elif isinstance(image_data, bytes):
                            return image_data

            print(f"No image found in response")
            return None

        except Exception as e:
            error_str = str(e)
            # Handle quota exceeded error
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                raise Exception(
                    "API quota exceeded. Please wait a minute and try again, "
                    "or check your Google Cloud quotas."
                )
            if "403" in error_str or "PERMISSION_DENIED" in error_str:
                raise Exception(
                    "Permission denied. Make sure you have enabled the Vertex AI API "
                    "and have proper authentication set up (gcloud auth application-default login)"
                )
            if "not available in your country" in error_str.lower():
                raise Exception(
                    "Image generation is not available in your region. "
                    "Try using a VPN or check Google's regional availability."
                )
            print(f"Image generation failed: {e}")
            raise

    def _build_image_prompt(self, graph_json: str, scene_name: str, style: str) -> str:
        """Build the prompt for image generation."""
        return f"""Generate a {style} view image of this scene: "{scene_name}"

The attached image shows a semantic graph where:
- Each node represents a location or element in the scene
- The node positions indicate their spatial relationships (top = north/up, bottom = south/down, left = west, right = east)
- Connected nodes are adjacent or linked areas

Scene graph data (JSON):
{graph_json}

Create a cohesive {style} illustration that:
1. Places each location/element according to its position in the graph
2. Shows connections between areas as paths, doors, or natural transitions
3. Uses appropriate visual elements for each node type (location, landmark, element, atmosphere)
4. Maintains consistent scale and perspective
5. Creates an immersive, game-ready scene

Generate the image now."""


class MockSceneImageGenerator:
    """Mock image generator for testing without API."""

    def __init__(self, api_key: str = "mock"):
        self.api_key = api_key

    def generate_scene_image(
        self,
        graph_json: str,
        graph_screenshot: bytes,
        scene_name: str = "scene",
        style: str = "top-down 2D game art"
    ) -> Optional[bytes]:
        """Return a placeholder image for testing."""
        # Create a simple placeholder PNG
        try:
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtGui import QImage, QPainter, QColor, QFont
            from PyQt6.QtCore import Qt, QRect, QBuffer, QIODevice

            # Create a placeholder image
            img = QImage(512, 512, QImage.Format.Format_RGB32)
            img.fill(QColor("#2d5016"))  # Dark green background

            painter = QPainter(img)
            painter.setPen(QColor("#ffffff"))
            painter.setFont(QFont("Arial", 16))

            # Draw placeholder text
            painter.drawText(
                QRect(0, 0, 512, 512),
                Qt.AlignmentFlag.AlignCenter,
                f"[Rendered Scene]\n{scene_name}\n\n(Mock - Add API key\nfor real generation)"
            )

            # Draw a simple border
            painter.setPen(QColor("#4a7c23"))
            painter.drawRect(10, 10, 492, 492)

            painter.end()

            # Convert to PNG bytes using QBuffer
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            img.save(buffer, "PNG")
            return bytes(buffer.data())

        except Exception as e:
            print(f"Mock image generation failed: {e}")
            return None
