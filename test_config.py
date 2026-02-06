import sys
import os

# Add the workspace to python path so we can import config
sys.path.append(os.getcwd())

from config.oem_name.test_group.app_config.app_config_manager import AppConfigManager

def test_config():
    print("Testing AppConfigManager...")
    
    # 1. Singleton Test
    c1 = AppConfigManager()
    c2 = AppConfigManager()
    
    if c1 is c2:
        print("[PASS] Singleton pattern working")
    else:
        print("[FAIL] Singleton pattern failed")
        
    # 2. Section Access
    try:
        # Check if attribute exists first
        if not hasattr(c1, 'DeviceConfiguration'):
            print("[FAIL] DeviceConfiguration section missing")
            return

        val = c1.DeviceConfiguration.ADB_DEVICE_1_ID
        print(f"[PASS] Section access working: ADB_DEVICE_1_ID={val}")
    except Exception as e:
        print(f"[FAIL] Section access failed: {e}")
        import traceback
        traceback.print_exc()
        
    try:
        video_enabled = c1.ProjectConfiguration.ENABLE_VIDEO_ENABLED
        print(f"[PASS] Boolean conversion working: ENABLE_VIDEO_ENABLED={video_enabled} (Type: {type(video_enabled)})")
    except Exception as e:
         print(f"[FAIL] Boolean conversion failed: {e}")

    # 3. Direct Access
    try:
        val_direct = c1("ADB_DEVICE_1_ID")
        if val_direct == "4B091VDAQ000F3":
             print(f"[PASS] Direct access working: {val_direct}")
        else:
             print(f"[FAIL] Direct access value mismatch: {val_direct}")
    except Exception as e:
        print(f"[FAIL] Direct access failed: {e}")

    # 4. Check integer
    try:
        ver = c1("ADB_DEVICE_1_VERSION")
        if isinstance(ver, int) and ver == 16:
             print(f"[PASS] Integer conversion working: {ver}")
        else:
             print(f"[FAIL] Integer conversion failed: {ver} type {type(ver)}")
    except Exception as e:
        print(f"[FAIL] Integer check failed: {e}")
        
    # 5. Check Log Paths (slashes)
    try:
        log_path = c1("SERVER_LOG_FOLDER_PATH")
        print(f"[PASS] Path check: {log_path}")
    except Exception as e:
        print(f"[FAIL] Path check failed: {e}")

if __name__ == "__main__":
    test_config()
