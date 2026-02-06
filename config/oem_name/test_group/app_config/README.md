# AppConfigManager Developer Guide

This guide explains how to modify the configuration for the automation framework.

## Configuration File
The configuration is stored in `config.txt` located in this directory.

## How Class Names are Decided
The `AppConfigManager` dynamically creates classes based on the **Section Headers** in `config.txt`.

The logic represents:
1. It reads a line starting with `#` (e.g., `# Device Configuration`).
2. It strips the `#` and whitespace.
3. It **removes all spaces** to form a valid Python class name.

**Example:**
- `# Device Configuration` -> `DeviceConfiguration` class.
- `# Project Configuration` -> `ProjectConfiguration` class.
- `# My New Section` -> `MyNewSection` class.

## How to Add New Configurations

### 1. Adding a New Data Member to an Existing Section
Simply add a new `KEY=VALUE` line under the appropriate section header.

**Example**: Adding `RETRY_COUNT` to `Project Configuration`.
```ini
# =========================
# Project Configuration
# =========================
ENABLE_VIDEO_ENABLED=NO
...
RETRY_COUNT=3  <-- Added this line
```
**Access in Code:**
```python
config.ProjectConfiguration.RETRY_COUNT
# OR
config("RETRY_COUNT")
```

### 2. Adding a New Section
1. Add a separator (optional, but good for readability).
2. Add a line starting with `# [Your Section Name]`.
3. Add your keys below it.

**Example**:
```ini
# =========================
# Database Settings
# =========================
DB_HOST=localhost
DB_PORT=5432
```

**Access in Code:**
```python
# The class name becomes 'DatabaseSettings' (spaces removed)
print(config.DatabaseSettings.DB_HOST)
```

## Data Types
The manager automatically detects:
- **Booleans**: `TRUE`, `FALSE`, `YES`, `NO`, `ON`, `OFF` (case-insensitive).
- **Integers**: `123`, `0`.
- **Floats**: `12.34`.
- **Strings**: Everything else.
