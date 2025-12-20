"""Settings manager for persistent configuration."""
import json
import os
from pathlib import Path
from typing import Optional, Any


class Settings:
    """
    Manages persistent application settings.
    Stores settings in a JSON file in the user's app data directory.
    """

    def __init__(self):
        self._settings_dir = self._get_settings_dir()
        self._settings_file = self._settings_dir / "settings.json"
        self._settings = self._load_settings()

    def _get_settings_dir(self) -> Path:
        """Get the settings directory, creating it if needed."""
        # Use AppData on Windows, ~/.config on Linux/Mac
        if os.name == 'nt':  # Windows
            base = Path(os.environ.get('APPDATA', Path.home()))
        else:
            base = Path.home() / '.config'

        settings_dir = base / 'SceneSynth'
        settings_dir.mkdir(parents=True, exist_ok=True)
        return settings_dir

    def _load_settings(self) -> dict:
        """Load settings from file."""
        if self._settings_file.exists():
            try:
                with open(self._settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_settings(self) -> None:
        """Save settings to file."""
        try:
            with open(self._settings_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a setting value and save."""
        self._settings[key] = value
        self._save_settings()

    def delete(self, key: str) -> None:
        """Delete a setting."""
        if key in self._settings:
            del self._settings[key]
            self._save_settings()

    # Convenience properties for common settings
    @property
    def api_key(self) -> Optional[str]:
        """Get the stored API key."""
        return self.get('api_key')

    @api_key.setter
    def api_key(self, value: Optional[str]) -> None:
        """Set the API key."""
        if value:
            self.set('api_key', value)
        else:
            self.delete('api_key')

    @property
    def last_project_path(self) -> Optional[str]:
        """Get the last opened project path."""
        return self.get('last_project_path')

    @last_project_path.setter
    def last_project_path(self, value: Optional[str]) -> None:
        """Set the last project path."""
        if value:
            self.set('last_project_path', value)
        else:
            self.delete('last_project_path')

    @property
    def render_style(self) -> str:
        """Get the last used render style."""
        return self.get('render_style', 'top-down 2D game art style, clean lines, vibrant colors')

    @render_style.setter
    def render_style(self, value: str) -> None:
        """Set the render style."""
        if value:
            self.set('render_style', value)

    @property
    def vertex_project_id(self) -> Optional[str]:
        """Get the Vertex AI project ID."""
        return self.get('vertex_project_id')

    @vertex_project_id.setter
    def vertex_project_id(self, value: Optional[str]) -> None:
        """Set the Vertex AI project ID."""
        if value:
            self.set('vertex_project_id', value)
        else:
            self.delete('vertex_project_id')


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
