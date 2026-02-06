import os

class AppConfigManager:
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AppConfigManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_path=None):
        if self._initialized:
            return
        
        self._global_map = {}
        
        if config_path is None:
            # Assume config.txt is in the same directory as this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, 'config.txt')
            
        self._load_config(config_path)
        self._initialized = True

    def _load_config(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found at {path}")

        current_section = None
        config_data = {}
        
        with open(path, 'r') as f:
            lines = f.readlines()
            
        in_comment = False
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Handle XML-style comments
            if in_comment:
                if "-->" in line:
                    in_comment = False
                continue

            if "<!--" in line:
                if "-->" in line:
                    # Inline/Single-line comment: Remove the comment part
                    start = line.find("<!--")
                    end = line.find("-->") + 3
                    line = (line[:start] + line[end:]).strip()
                    if not line:
                        continue
                else:
                    # Start of multi-line comment
                    in_comment = True
                    continue
                
            if line.startswith("#"):
                # Check for separator lines to ignore
                if "=====" in line:
                    continue
                
                # Parse section name from comment e.g., "# Device Configuration"
                section_title = line.lstrip("#").strip()
                if section_title:
                    # Remove spaces for class name compatibility
                    current_section = section_title.replace(" ", "")
                    if current_section not in config_data:
                        config_data[current_section] = {}
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
            # The data dictionary becomes the class attributes
            section_class = type(section_name, (object,), data)
            setattr(self, section_name, section_class)

    def _parse_value(self, value):
        # Handle Booleans
        lower_val = value.lower()
        if lower_val in ('true', 'yes', 'on'):
            return True
        if lower_val in ('false', 'no', 'off'):
            return False
            
        # Handle Numbers
        if value.isdigit():
            return int(value)
        try:
            return float(value)
        except ValueError:
            pass
            
        # Return string
        return value

    def __call__(self, key):
        """Allow calling the instance to get a config value directly."""
        if key in self._global_map:
            return self._global_map[key]
        raise KeyError(f"Key '{key}' not found in configuration")
