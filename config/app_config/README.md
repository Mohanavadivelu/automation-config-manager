# AppConfigManager Developer Guide

This guide explains how to manage and modify the **Multi-Project Configuration** for the automation framework.

## Directory Structure
```text
config/app_config/
├── app_config_manager.py   # The Singleton Manager
├── settings.env            # Persistent storage (Stores DEFAULT_PROJECT)
└── projects/               # Directory containing Project Configurations
    ├── ferrari.env         # Configuration for Ferrari project
    ├── audi.env            # Configuration for Audi project
    └── ...
```

## 1. Projects
Each project has its own `.env` file located in the `projects/` directory.

### Adding a New Project
1. Create a new file `projects/<project_name>.env`.
2. Add your configuration sections and keys.

### Configuration Format
Files use a standard `KEY=VALUE` format with **Section Headers**.

```ini
# =========================
#class Device Configuration
# =========================
ADB_DEVICE_1_ID=4B091VDAQ000F3

# =========================
#class Project Configuration
# =========================
EXECUTE_GROUP=FERRARI_PCTS
```

## 2. Dynamic Switching
The `AppConfigManager` supports switching projects at runtime. The selection is **persistent** (saved to `settings.env`).

### API Usage
```python
# Convenience imports via __init__.py
from config.app_config import AppConfigManager

config = AppConfigManager()

# 1. Get List of Available Projects
# Returns: ['ferrari', 'audi']
projects = config.get_available_projects()

# 2. Switch Project
# This updates settings.env and reloads the configuration immediately.
config.set_default_project("audi")

# 3. Access Config Values
print(config.ProjectConfiguration.EXECUTE_GROUP)
```

## 3. Error Handling (Custom Exceptions)
The manager raises custom exceptions for common error scenarios:

- **Missing project file**: `ProjectNotFoundError` (subclasses `FileNotFoundError`)
- **Missing key** when using the callable accessor (`config("KEY")`): `ConfigKeyNotFoundError` (subclasses `KeyError`)
- **Invalid project name**: `InvalidProjectNameError` (subclasses `ValueError`) — raised when a project name contains path traversal sequences (`../`, `..`), slashes, spaces, or other disallowed characters. Valid names may only contain alphanumeric characters, hyphens, underscores, plus signs, and dots (e.g. `ferrari`, `tata_gen3+`, `v1.2`). Names must not start with `.` or contain `..`.

```python
from config.app_config import (
    AppConfigManager,
    ProjectNotFoundError,
    ConfigKeyNotFoundError,
    InvalidProjectNameError,
)

config = AppConfigManager()

try:
    config.load_project("does_not_exist")
except ProjectNotFoundError as e:
    print(e)

try:
    value = config("SOME_MISSING_KEY")
except ConfigKeyNotFoundError as e:
    print(e)

try:
    config.load_project("../../etc/passwd")
except InvalidProjectNameError as e:
    print(e)  # "Invalid project name '../../etc/passwd'. Only alphanumeric..."
```

## 4. Class Names Logic
The Manager dynamically creates classes based on precise **Section definitions**.
- `#class Device Configuration` -> `config.DeviceConfiguration`
- Lines starting with `#` but **not** `#class` are treated as comments and ignored.

## 5. Data Types
The manager automatically detects:
- **Booleans**: `TRUE`, `FALSE`, `YES`, `NO`, `ON`, `OFF` (case-insensitive).
- **Integers**: `123`, `0`, `-1`, `+5` (supports `+`/`-` prefixes).
- **Floats**: `12.34`, `-0.5`, `+2.7`, `1e3`, `2.5e-1` (including scientific notation).
- **Strings**: Everything else (including `inf`, `-inf`, `nan`, version strings like `0.0.1`).
- **Empty values**: `KEY=` returns an empty string `""`.

## 6. Thread Safety
The `AppConfigManager` singleton uses a **thread-safe double-checked locking** pattern. Multiple threads can safely call `AppConfigManager()` concurrently and will always receive the same singleton instance.
