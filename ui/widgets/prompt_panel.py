"""PromptPanel - Side panel for natural language interaction."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton,
    QLabel, QComboBox, QSpinBox, QHBoxLayout, QGroupBox
)
from PyQt6.QtCore import Qt

from config import DEFAULT_NODE_COUNT, MIN_NODE_COUNT, MAX_NODE_COUNT


class PromptPanel(QWidget):
    """
    Side panel for natural language interaction with the graph.

    Features:
    - Master prompt input for new graphs
    - Modification prompt input for existing graphs
    - Preset prompt suggestions
    - Generation settings (node count, etc.)
    """

    def __init__(self, app_state=None):
        super().__init__()
        self.app_state = app_state
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Master Prompt Section
        gen_group = QGroupBox("Generate New Graph")
        gen_layout = QVBoxLayout(gen_group)

        gen_layout.addWidget(QLabel("Master Prompt:"))
        self.master_prompt_input = QTextEdit()
        self.master_prompt_input.setPlaceholderText(
            "Describe your world, region, or scene...\n\n"
            "Examples:\n"
            "- A medieval fantasy world with rolling hills, ancient forests, and scattered villages\n"
            "- A cyberpunk city district with neon-lit streets and underground markets\n"
            "- A haunted mansion with secret passages and forgotten rooms"
        )
        self.master_prompt_input.setMaximumHeight(120)
        gen_layout.addWidget(self.master_prompt_input)

        # Generation settings
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(QLabel("Nodes:"))
        self.node_count_spin = QSpinBox()
        self.node_count_spin.setRange(MIN_NODE_COUNT, MAX_NODE_COUNT)
        self.node_count_spin.setValue(DEFAULT_NODE_COUNT)
        self.node_count_spin.setToolTip("Number of nodes to generate")
        settings_layout.addWidget(self.node_count_spin)
        settings_layout.addStretch()
        gen_layout.addLayout(settings_layout)

        # Generate button
        self.generate_btn = QPushButton("Generate Graph")
        self.generate_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.generate_btn.clicked.connect(self._on_generate)
        gen_layout.addWidget(self.generate_btn)

        layout.addWidget(gen_group)

        # Modification Section
        mod_group = QGroupBox("Modify Current Graph")
        mod_layout = QVBoxLayout(mod_group)

        mod_layout.addWidget(QLabel("Modification Prompt:"))
        self.modify_prompt_input = QTextEdit()
        self.modify_prompt_input.setPlaceholderText(
            "Describe changes to make...\n\n"
            "Examples:\n"
            "- Add a tavern connected to the market square\n"
            "- Remove the dungeon\n"
            "- Make the forest larger and more mysterious\n"
            "- Add a secret passage between the library and the cellar"
        )
        self.modify_prompt_input.setMaximumHeight(100)
        mod_layout.addWidget(self.modify_prompt_input)

        self.modify_btn = QPushButton("Apply Changes")
        self.modify_btn.setStyleSheet("background-color: #2196F3; color: white;")
        self.modify_btn.clicked.connect(self._on_modify)
        mod_layout.addWidget(self.modify_btn)

        layout.addWidget(mod_group)

        # Quick Actions Section
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout(actions_group)

        self.quick_actions = QComboBox()
        self.quick_actions.addItems([
            "Select an action...",
            "Add connecting paths between isolated nodes",
            "Add more detail to the scene",
            "Simplify graph structure",
            "Add atmospheric elements (weather, time of day)",
            "Add NPCs/characters to locations",
            "Create entrance and exit points"
        ])
        actions_layout.addWidget(self.quick_actions)

        apply_action_btn = QPushButton("Apply Quick Action")
        apply_action_btn.clicked.connect(self._on_quick_action)
        actions_layout.addWidget(apply_action_btn)

        layout.addWidget(actions_group)

        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addStretch()

    def _on_generate(self) -> None:
        """Handle generate button click."""
        prompt = self.master_prompt_input.toPlainText().strip()
        if not prompt:
            self.status_label.setText("Please enter a prompt")
            self.status_label.setStyleSheet("color: #f44336;")
            return

        if self.app_state:
            node_count = self.node_count_spin.value()
            self.status_label.setText("Generating...")
            self.status_label.setStyleSheet("color: #2196F3;")
            self.generate_btn.setEnabled(False)

            # Call app state to generate
            self.app_state.generate_graph(prompt, node_count)

            # Re-enable after generation (would be done via signal in real async)
            self.generate_btn.setEnabled(True)
            self.status_label.setText("Generation complete")
            self.status_label.setStyleSheet("color: #4CAF50;")

    def _on_modify(self) -> None:
        """Handle modify button click."""
        instruction = self.modify_prompt_input.toPlainText().strip()
        if not instruction:
            self.status_label.setText("Please enter a modification instruction")
            self.status_label.setStyleSheet("color: #f44336;")
            return

        if not self.app_state or not self.app_state.current_graph:
            self.status_label.setText("No graph to modify")
            self.status_label.setStyleSheet("color: #f44336;")
            return

        self.status_label.setText("Applying changes...")
        self.status_label.setStyleSheet("color: #2196F3;")
        self.modify_btn.setEnabled(False)

        # Call app state to modify
        if self.app_state:
            self.app_state.modify_graph(instruction)

        self.modify_btn.setEnabled(True)
        self.status_label.setText("Changes applied")
        self.status_label.setStyleSheet("color: #4CAF50;")

    def _on_quick_action(self) -> None:
        """Handle quick action selection."""
        action = self.quick_actions.currentText()
        if action == "Select an action...":
            return

        # Map actions to prompts
        action_prompts = {
            "Add connecting paths between isolated nodes":
                "Add paths or connections between any isolated nodes that aren't connected to others",
            "Add more detail to the scene":
                "Add more interesting details and sub-locations to existing areas",
            "Simplify graph structure":
                "Simplify the graph by removing less important nodes and consolidating connections",
            "Add atmospheric elements (weather, time of day)":
                "Add atmospheric nodes like weather conditions, lighting, or time-of-day elements",
            "Add NPCs/characters to locations":
                "Add character nodes representing NPCs, guards, merchants, or inhabitants",
            "Create entrance and exit points":
                "Add entrance and exit nodes to the scene for navigation"
        }

        prompt = action_prompts.get(action)
        if prompt:
            self.modify_prompt_input.setPlainText(prompt)
            self._on_modify()

        # Reset combo
        self.quick_actions.setCurrentIndex(0)

    def trigger_generate(self) -> None:
        """Trigger generation (called from toolbar)."""
        self._on_generate()

    def set_status(self, message: str, is_error: bool = False) -> None:
        """Set the status message."""
        self.status_label.setText(message)
        if is_error:
            self.status_label.setStyleSheet("color: #f44336;")
        else:
            self.status_label.setStyleSheet("color: #4CAF50;")
