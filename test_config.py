import sys
import os

# Add the workspace to python path so we can import config
sys.path.append(os.getcwd())

from config.app_config.app_config_manager import AppConfigManager
from config.app_config.app_config_manager import (
    ProjectNotFoundError,
    ConfigKeyNotFoundError,
    InvalidProjectNameError,
)

# Also verify the __init__.py convenience imports work
from config.app_config import (
    AppConfigManager as AcmFromInit,
    InvalidProjectNameError as IpneFromInit,
)


def test_config():
    print("=" * 60)
    print("Testing AppConfigManager Improvements")
    print("=" * 60)

    # ----------------------------------------------------------------
    # 1. __init__.py convenience imports
    # ----------------------------------------------------------------
    print("\n--- Test 1: __init__.py exports ---")
    assert AcmFromInit is AppConfigManager, "Import mismatch"
    assert IpneFromInit is InvalidProjectNameError, "Import mismatch"
    print("[PASS] __init__.py exports AppConfigManager & all exceptions")

    # ----------------------------------------------------------------
    # 2. Singleton & Initial Load (ferrari from settings.env)
    # ----------------------------------------------------------------
    print("\n--- Test 2: Singleton & Initial Load ---")
    c1 = AppConfigManager()
    print(f"Available Projects: {c1.get_available_projects()}")

    try:
        val = c1.ProjectConfiguration.EXECUTE_GROUP
        print(f"[PASS] Initial Load (ferrari): EXECUTE_GROUP={val}")
    except Exception as e:
        print(f"[FAIL] Initial Load failed: {e}")

    # ----------------------------------------------------------------
    # 3. Dynamic Switching
    # ----------------------------------------------------------------
    print("\n--- Test 3: Dynamic Switching ---")
    audi_path = os.path.join(c1.projects_dir, "audi.env")
    with open(audi_path, 'w') as f:
        f.write("#class Project Configuration\nEXECUTE_GROUP=AUDI_PCTS\n")

    try:
        print("Switching to 'audi'...")
        c1.set_default_project("audi")

        with open(c1.settings_file, 'r') as f:
            content = f.read().strip()
        print(f"Settings file content: {content}")
        if "DEFAULT_PROJECT=audi" in content:
            print("[PASS] Persistence file updated")
        else:
            print("[FAIL] Persistence file not updated")

        val = c1.ProjectConfiguration.EXECUTE_GROUP
        if val == "AUDI_PCTS":
            print(f"[PASS] Switched to Audi: EXECUTE_GROUP={val}")
        else:
            print(f"[FAIL] Switch failed, val={val}")

    except Exception as e:
        print(f"[FAIL] Switching failed: {e}")

    # ----------------------------------------------------------------
    # 4. Persistence Check
    # ----------------------------------------------------------------
    print("\n--- Test 4: Persistence Check ---")
    default = c1._get_persistent_default()
    if default == "audi":
        print("[PASS] _get_persistent_default returns 'audi'")
    else:
        print(f"[FAIL] _get_persistent_default returned {default}")

    # Cleanup: Switch back to ferrari and delete audi
    c1.set_default_project("ferrari")
    if os.path.exists(audi_path):
        os.remove(audi_path)
    print("Restored to ferrari and cleaned up.")

    # ----------------------------------------------------------------
    # 5. Custom exception: ProjectNotFoundError
    # ----------------------------------------------------------------
    print("\n--- Test 5: ProjectNotFoundError ---")
    try:
        c1.load_project("does_not_exist")
        print("[FAIL] Expected ProjectNotFoundError was not raised")
    except ProjectNotFoundError:
        print("[PASS] Missing project raises ProjectNotFoundError")

    # ----------------------------------------------------------------
    # 6. Custom exception: ConfigKeyNotFoundError
    # ----------------------------------------------------------------
    print("\n--- Test 6: ConfigKeyNotFoundError ---")
    try:
        _ = c1("__missing_key__")
        print("[FAIL] Expected ConfigKeyNotFoundError was not raised")
    except ConfigKeyNotFoundError:
        print("[PASS] Missing key raises ConfigKeyNotFoundError")

    # ----------------------------------------------------------------
    # 7. Path traversal validation (Improvement #7)
    # ----------------------------------------------------------------
    print("\n--- Test 7: Path Traversal / Invalid Project Name Validation ---")
    malicious_names = [
        "../../etc/passwd",
        "../secret",
        "my project",       # spaces not allowed
        "project/sub",      # slashes not allowed
        "project\\sub",     # backslashes not allowed
        "",                 # empty string
        "hello world",
        ".hidden",          # starts with dot
        "a..b",             # consecutive dots (path traversal)
    ]
    all_blocked = True
    for name in malicious_names:
        try:
            c1.load_project(name)
            print(f"[FAIL] '{name}' was NOT blocked — expected InvalidProjectNameError")
            all_blocked = False
        except InvalidProjectNameError:
            print(f"[PASS] '{name}' correctly blocked")
        except ProjectNotFoundError:
            # Should not reach here — validation should fire first
            print(f"[FAIL] '{name}' raised ProjectNotFoundError instead of InvalidProjectNameError")
            all_blocked = False

    # Valid names should pass validation (even if file doesn't exist)
    valid_names = ["ferrari", "my-project", "project_v2", "Test123", "tata_gen3+", "v1.2"]
    for name in valid_names:
        try:
            c1.load_project(name)
            # If file doesn't exist, ProjectNotFoundError is fine — validation passed
            print(f"[PASS] '{name}' passed validation (loaded successfully)")
        except InvalidProjectNameError:
            print(f"[FAIL] '{name}' was incorrectly blocked by validation")
            all_blocked = False
        except ProjectNotFoundError:
            print(f"[PASS] '{name}' passed validation (file not found, which is expected)")

    # ----------------------------------------------------------------
    # 8. _parse_value edge cases (Improvement #6)
    # ----------------------------------------------------------------
    print("\n--- Test 8: _parse_value Edge Cases ---")
    pv = c1._parse_value

    # Empty string
    assert pv("") == "", f"Expected '', got {pv('')!r}"
    print("[PASS] Empty string returns ''")

    # Booleans (case-insensitive)
    assert pv("TRUE") is True
    assert pv("false") is False
    assert pv("Yes") is True
    assert pv("NO") is False
    assert pv("on") is True
    assert pv("OFF") is False
    print("[PASS] Booleans parsed correctly")

    # Positive integers
    assert pv("0") == 0
    assert pv("42") == 42
    assert pv("007") == 7
    print("[PASS] Positive integers parsed correctly")

    # Negative integers
    assert pv("-1") == -1
    assert pv("-999") == -999
    print("[PASS] Negative integers parsed correctly")

    # Plus-prefixed integers
    assert pv("+5") == 5
    assert pv("+100") == 100
    print("[PASS] Plus-prefixed integers parsed correctly")

    # Floats
    assert pv("3.14") == 3.14
    assert pv("-0.5") == -0.5
    assert pv("+2.7") == 2.7
    print("[PASS] Floats parsed correctly")

    # Scientific notation
    assert pv("1e3") == 1000.0
    assert pv("2.5e-1") == 0.25
    print("[PASS] Scientific notation parsed correctly")

    # inf / nan should remain as strings
    assert pv("inf") == "inf"
    assert pv("-inf") == "-inf"
    assert pv("nan") == "nan"
    print("[PASS] inf/nan kept as strings")

    # Regular strings
    assert pv("hello") == "hello"
    assert pv("/some/path") == "/some/path"
    assert pv("0.0.1") == "0.0.1"  # version string, not a float
    print("[PASS] Regular strings returned as-is")

    # ----------------------------------------------------------------
    # 9. Thread safety (Improvement #5) — basic verification
    # ----------------------------------------------------------------
    print("\n--- Test 9: Thread Safety ---")
    import threading

    instances = []
    errors = []

    def create_instance():
        try:
            inst = AppConfigManager()
            instances.append(id(inst))
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=create_instance) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    unique_ids = set(instances)
    if len(unique_ids) == 1 and not errors:
        print(f"[PASS] 20 threads all got the same singleton instance (id={unique_ids.pop()})")
    else:
        print(f"[FAIL] Got {len(unique_ids)} unique instances, errors: {errors}")

    # ----------------------------------------------------------------
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_config()
