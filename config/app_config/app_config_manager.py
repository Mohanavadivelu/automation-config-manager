import os
import re
import threading


class AppConfigError(Exception):
    """Base exception for configuration-related errors."""


class ProjectNotFoundError(AppConfigError, FileNotFoundError):
    """Raised when a requested project config file does not exist."""


class ConfigKeyNotFoundError(AppConfigError, KeyError):
    """Raised when a requested configuration key is not present."""

class InvalidProjectNameError(AppConfigError, ValueError):
    """Raised when a project name contains invalid characters or path traversal."""


class AppConfigManager:
    _instance = None
    _initialized = False
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                # Double-checked locking to prevent race conditions
                if not cls._instance:
                    cls._instance = super(AppConfigManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.app_config_dir = os.path.dirname(os.path.abspath(__file__))
        self.projects_dir = os.path.join(self.app_config_dir, 'projects')
        self.settings_file = os.path.join(self.app_config_dir, 'settings.env')
        
        # Track dynamically-created section attributes so we can safely unload
        # them on reload without accidentally deleting legitimate attributes.
        self._loaded_sections = set()

        # Initial load
        default_project = self._get_persistent_default()
        self.load_project(default_project)
        
        self._initialized = True

    def _get_persistent_default(self):
        """Read settings.env to find DEFAULT_PROJECT."""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    for line in f:
                        if line.startswith("DEFAULT_PROJECT="):
                            return line.split("=", 1)[1].strip()
            except Exception:
                pass # Ignore errors, fallback
        
        # Fallback logic: return first available project or 'default'
        available = self.get_available_projects()
        if available:
            return available[0]
        return "default"

    def get_available_projects(self):
        """Return a list of available project names (files in projects/ dir)."""
        if not os.path.exists(self.projects_dir):
            return []
            
        projects = []
        for f in os.listdir(self.projects_dir):
            if f.endswith(".env"):
                projects.append(f[:-4]) # Remove .env extension
        return projects

    @staticmethod
    def _validate_project_name(project_name):
        """Validate project name to prevent path traversal and invalid characters.

        A valid project name contains only alphanumeric characters, hyphens,
        underscores, plus signs, and dots — but must not start with a dot
        and must not contain consecutive dots (e.g. 'ferrari', 'my-project',
        'project_v2', 'tata_gen3+', 'v1.2').

        Raises:
            InvalidProjectNameError: If the name is empty, starts with a dot,
                contains '..' (path traversal), or has disallowed characters
                such as '/' or '\\'.
        """
        if (
            not project_name
            or project_name.startswith('.')
            or '..' in project_name
            or not re.match(r'^[a-zA-Z0-9_\-+.]+$', project_name)
        ):
            raise InvalidProjectNameError(
                f"Invalid project name '{project_name}'. "
                "Only alphanumeric characters, hyphens, underscores, "
                "plus signs, and dots are allowed. Must not start with '.' "
                "or contain '..'."
            )

    def set_default_project(self, project_name):
        """Update settings.env and reload configuration."""
        self._validate_project_name(project_name)

        # 1. Update Persistent File
        with open(self.settings_file, 'w') as f:
            f.write(f"DEFAULT_PROJECT={project_name}\n")
            
        # 2. Reload
        self.load_project(project_name)

    def load_project(self, project_name):
        """Load configuration from specific project file."""
        self._validate_project_name(project_name)
        config_path = os.path.join(self.projects_dir, f"{project_name}.env")
        
        # Reset current state
        self._global_map = {}
        # Clear only previously loaded dynamic sections to avoid stale data.
        for section_name in list(self._loaded_sections):
            if hasattr(self, section_name):
                delattr(self, section_name)
        self._loaded_sections.clear()

        self._load_config_file(config_path)

    def _load_config_file(self, path):
        if not os.path.exists(path):
            raise ProjectNotFoundError(f"Config file not found at {path}")

        current_section = None
        config_data = {}
        
        with open(path, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("#"):
                # Handle Explicit Class Definitions
                # Format: #class Device Configuration
                if line.startswith("#class "):
                     section_title = line[7:].strip() # Remove "#class "
                     if section_title:
                        # Remove spaces for class name compatibility
                        current_section = section_title.replace(" ", "")
                        if current_section not in config_data:
                            config_data[current_section] = {}
                # All other lines starting with # are comments and ignored
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = self._parse_value(value.strip())
                
                # Add to global map for direct access
                self._global_map[key] = value
                
                # Add to section data
                if current_section:
                    config_data[current_section][key] = value

        # Create section classes and attach to self
        for section_name, data in config_data.items():
            # Create a dynamic class for the section
            section_class = type(section_name, (object,), data)
            setattr(self, section_name, section_class)
            self._loaded_sections.add(section_name)

    def _parse_value(self, value):
        # Handle empty values
        if not value:
            return value

        # Handle Booleans
        lower_val = value.lower()
        if lower_val in ('true', 'yes', 'on'):
            return True
        if lower_val in ('false', 'no', 'off'):
            return False

        # Handle Numbers
        # Use regex to match integers: optional +/- sign followed by digits.
        if re.match(r'^[+-]?\d+$', value):
            return int(value)
        # Try float conversion (handles decimals, scientific notation, +/- prefix).
        try:
            float_val = float(value)
            # Guard against values like 'inf', '-inf', 'nan' being treated as
            # floats — keep them as strings for safety.
            import math
            if math.isfinite(float_val):
                return float_val
        except ValueError:
            pass

        # Return string
        return value

    def __call__(self, key):
        """Allow calling the instance to get a config value directly."""
        if key in self._global_map:
            return self._global_map[key]
        raise ConfigKeyNotFoundError(f"Key '{key}' not found in configuration")
