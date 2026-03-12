import sys
import os
import winreg
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def register_extension(ext, prog_id):
    try:
        # Register in HKCU (no admin needed usually)
        key_path = f"Software\\Classes\\{ext}\\OpenWithProgids"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, prog_id, 0, winreg.REG_NONE, b"")
        print(f"Registered {ext}")
    except Exception as e:
        print(f"Failed to register {ext}: {e}")

def main():
    # Path to python executable (pythonw.exe to hide console)
    python_exe = sys.executable.replace("python.exe", "pythonw.exe")
    if not os.path.exists(python_exe):
        python_exe = sys.executable # Fallback

    # Path to main.py
    script_path = os.path.abspath("main.py")
    
    prog_id = "PrismView.HEIC"
    app_name = "PrismView"
    
    # 1. Create ProgID
    try:
        key_path = f"Software\\Classes\\{prog_id}"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, app_name)
            
        # Add DefaultIcon
        icon_path = f"{key_path}\\DefaultIcon"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, icon_path) as key:
            # Use python executable icon or a custom .ico if you have one
            winreg.SetValue(key, "", winreg.REG_SZ, f'"{python_exe}",0')
            
        cmd_path = f"{key_path}\\shell\\open\\command"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, cmd_path) as key:
            command = f'"{python_exe}" "{script_path}" "%1"'
            winreg.SetValue(key, "", winreg.REG_SZ, command)
            
        print(f"Created ProgID: {prog_id}")
    except Exception as e:
        print(f"Failed to create ProgID: {e}")
        return

    # 2. Register extensions
    extensions = [".png", ".jpg", ".jpeg", ".bmp", ".gif", ".heic"]
    for ext in extensions:
        register_extension(ext, prog_id)

    print("\nRegistration complete. You should now see 'PrismView' in the 'Open with' menu for these files.")
    print("If not, you may need to restart Explorer or choose 'Choose another app' and find it in the list.")

if __name__ == "__main__":
    main()
