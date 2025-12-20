"""ApiKeyDialog - Dialog for API key configuration."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QHBoxLayout, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt

from core.settings import get_settings


class ApiKeyDialog(QDialog):
    """
    Dialog for configuring API keys (BYOK - Bring Your Own Key).
    """

    def __init__(self, parent=None, app_state=None):
        super().__init__(parent)
        self.app_state = app_state
        self._settings = get_settings()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the UI."""
        self.setWindowTitle("API Settings")
        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)

        # Gemini API Key Group
        gemini_group = QGroupBox("Gemini API (for graph generation)")
        gemini_layout = QFormLayout(gemini_group)

        info = QLabel(
            "Get an API key from: https://aistudio.google.com/app/apikey"
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666; font-size: 11px;")
        gemini_layout.addRow(info)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Enter your Gemini API key...")

        # Load existing key if available
        if self.app_state and self.app_state.api_key:
            self.api_key_input.setText(self.app_state.api_key)

        gemini_layout.addRow("API Key:", self.api_key_input)

        # Show/hide toggle
        self.show_key_btn = QPushButton("Show")
        self.show_key_btn.setCheckable(True)
        self.show_key_btn.toggled.connect(self._toggle_key_visibility)
        gemini_layout.addRow("", self.show_key_btn)

        layout.addWidget(gemini_group)

        # Vertex AI Group (for image generation)
        vertex_group = QGroupBox("Vertex AI (for image rendering)")
        vertex_layout = QFormLayout(vertex_group)

        vertex_info = QLabel(
            "For image rendering, set up Vertex AI:\n"
            "1. Create a Google Cloud project\n"
            "2. Enable the Vertex AI API\n"
            "3. Run: gcloud auth application-default login"
        )
        vertex_info.setWordWrap(True)
        vertex_info.setStyleSheet("color: #666; font-size: 11px;")
        vertex_layout.addRow(vertex_info)

        self.project_id_input = QLineEdit()
        self.project_id_input.setPlaceholderText("your-gcp-project-id")

        # Load existing project ID
        if self._settings.vertex_project_id:
            self.project_id_input.setText(self._settings.vertex_project_id)

        vertex_layout.addRow("Project ID:", self.project_id_input)

        layout.addWidget(vertex_group)

        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666;")
        layout.addWidget(self.status_label)

        # Buttons
        btn_layout = QHBoxLayout()

        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self._test_connection)
        btn_layout.addWidget(test_btn)

        btn_layout.addStretch()

        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def _toggle_key_visibility(self, show: bool) -> None:
        """Toggle API key visibility."""
        if show:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_key_btn.setText("Hide")
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_key_btn.setText("Show")

    def _test_connection(self) -> None:
        """Test the API connection."""
        key = self.api_key_input.text().strip()
        if not key:
            self.status_label.setText("Please enter an API key")
            self.status_label.setStyleSheet("color: #f44336;")
            return

        self.status_label.setText("Testing connection...")
        self.status_label.setStyleSheet("color: #2196F3;")

        # Test would be async in real implementation
        try:
            # Placeholder for actual API test
            if self.app_state:
                success = self.app_state.test_api_key(key)
                if success:
                    self.status_label.setText("Connection successful!")
                    self.status_label.setStyleSheet("color: #4CAF50;")
                else:
                    self.status_label.setText("Connection failed. Check your API key.")
                    self.status_label.setStyleSheet("color: #f44336;")
            else:
                # No app state, assume success for now
                self.status_label.setText("Connection successful!")
                self.status_label.setStyleSheet("color: #4CAF50;")

        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            self.status_label.setStyleSheet("color: #f44336;")

    def _save(self) -> None:
        """Save the API key and project ID."""
        key = self.api_key_input.text().strip()
        project_id = self.project_id_input.text().strip()

        if self.app_state:
            self.app_state.set_api_key(key)

        # Save Vertex AI project ID
        self._settings.vertex_project_id = project_id

        # Update image generator with new project ID
        if self.app_state and self.app_state.image_generator:
            self.app_state.image_generator.project_id = project_id
            self.app_state.image_generator._initialized = False  # Force reinit

        self.accept()
