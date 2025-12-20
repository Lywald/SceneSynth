"""Render settings dialog."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QLineEdit, QPushButton, QGroupBox,
    QFormLayout
)
from PyQt6.QtCore import Qt

from core.settings import get_settings


# Preset styles for image generation
STYLE_PRESETS = {
    "Top-down 2D Game Art": "top-down 2D game art style, clean lines, vibrant colors",
    "Fantasy Illustration": "fantasy illustration style, detailed, painterly, magical atmosphere",
    "Photorealistic": "photorealistic style, highly detailed, realistic lighting and textures",
    "Pixel Art": "pixel art style, retro 16-bit aesthetic, limited color palette",
    "Watercolor": "watercolor painting style, soft edges, flowing colors, artistic",
    "Anime/Manga": "anime style, cel-shaded, vibrant, Japanese animation aesthetic",
    "Dark Fantasy": "dark fantasy style, moody lighting, gothic atmosphere, detailed",
    "Minimalist": "minimalist style, simple shapes, clean design, limited colors",
    "Isometric": "isometric view, 3D-like 2D perspective, game asset style",
    "Custom...": ""
}


class RenderDialog(QDialog):
    """Dialog for configuring render settings before generating an image."""

    def __init__(self, parent=None, current_style: str = "Top-down 2D Game Art"):
        super().__init__(parent)
        self._current_style = current_style
        self._setup_ui()
        self._load_style(current_style)

    def _setup_ui(self) -> None:
        """Set up the UI."""
        self.setWindowTitle("Render Scene")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Style settings group
        style_group = QGroupBox("Image Style")
        style_layout = QFormLayout(style_group)

        # Style preset dropdown
        self.style_combo = QComboBox()
        self.style_combo.addItems(STYLE_PRESETS.keys())
        self.style_combo.currentTextChanged.connect(self._on_preset_changed)
        style_layout.addRow("Preset:", self.style_combo)

        # Custom style textbox
        self.custom_style = QLineEdit()
        self.custom_style.setPlaceholderText("Enter custom style description...")
        style_layout.addRow("Style:", self.custom_style)

        layout.addWidget(style_group)

        # Info label
        info_label = QLabel(
            "The style describes how the AI will render your scene graph.\n"
            "Select a preset or enter a custom description."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(info_label)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        render_btn = QPushButton("Render")
        render_btn.setDefault(True)
        render_btn.clicked.connect(self.accept)
        btn_layout.addWidget(render_btn)

        layout.addLayout(btn_layout)

    def _on_preset_changed(self, preset_name: str) -> None:
        """Handle preset selection change."""
        if preset_name == "Custom...":
            self.custom_style.setEnabled(True)
            self.custom_style.setFocus()
        else:
            self.custom_style.setEnabled(True)
            self.custom_style.setText(STYLE_PRESETS.get(preset_name, ""))

    def _load_style(self, style: str) -> None:
        """Load a style into the dialog."""
        # Check if it matches a preset
        for preset_name, preset_style in STYLE_PRESETS.items():
            if preset_style == style:
                self.style_combo.setCurrentText(preset_name)
                self.custom_style.setText(style)
                return

        # Custom style
        self.style_combo.setCurrentText("Custom...")
        self.custom_style.setText(style)

    def get_style(self) -> str:
        """Get the selected style."""
        return self.custom_style.text().strip() or "top-down 2D game art"

    @staticmethod
    def get_render_style(parent=None) -> tuple:
        """
        Show the dialog and return (style, accepted).
        Loads and saves the style preference automatically.

        Returns:
            Tuple of (style_string, was_accepted)
        """
        settings = get_settings()
        saved_style = settings.render_style

        dialog = RenderDialog(parent, saved_style)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            style = dialog.get_style()
            settings.render_style = style  # Save for next time
            return style, True

        return "", False
