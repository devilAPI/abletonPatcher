import json
import re
import os
import sys
import ctypes
import platform
import subprocess

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def run_as_admin():
    script = os.path.abspath(sys.argv[0])
    params = subprocess.list2cmdline(sys.argv[1:])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
    sys.exit(0)

def find_installations():
    system = platform.system()
    installations = []
    
    if system == "Windows":
        base_dir = "C:\\ProgramData\\Ableton"
        if not os.path.exists(base_dir):
            return installations
            
        for entry in os.listdir(base_dir):
            if "Live" in entry:
                entry_path = os.path.join(base_dir, entry)
                if os.path.isdir(entry_path):
                    program_dir = os.path.join(entry_path, "Program")
                    if os.path.exists(program_dir):
                        for file in os.listdir(program_dir):
                            if file.endswith(".exe") and "Live" in file:
                                exe_path = os.path.join(program_dir, file)
                                installations.append((exe_path, entry))
    
    elif system == "Darwin":
        base_dir = "/Applications"
        if not os.path.exists(base_dir):
            return installations
            
        for entry in os.listdir(base_dir):
            if entry.endswith(".app") and "Ableton Live" in entry:
                app_path = os.path.join(base_dir, entry)
                exe_path = os.path.join(app_path, "Contents", "MacOS", "Live")
                if os.path.exists(exe_path):
                    name = entry.replace(".app", "")
                    installations.append((exe_path, name))
    
    return installations

def load_config(json_file_path):
    """Load configuration and handle auto path detection"""
    try:
        with open(json_file_path, 'r') as json_file:
            data = json.load(json_file)
            file_path = data.get("file_path")
            new_signkey = data.get("old_signkey")
            old_signkey = data.get("new_signkey")

            if not file_path or not old_signkey or not new_signkey:
                raise ValueError("JSON file must contain 'file_path', 'old_signkey', and 'new_signkey'.")

            if file_path.lower() == "auto":
                installations = find_installations()
                if not installations:
                    print("\nNo Ableton Live installations found. Please specify the path manually.")
                    input("Press Enter to exit...")
                    sys.exit(1)

                print("\nFound Ableton installations:")
                for i, (path, name) in enumerate(installations):
                    print(f"{i+1}. {name} at {path}")

                try:
                    selection = int(input("\nSelect installation to patch: ")) - 1
                    if selection < 0 or selection >= len(installations):
                        print("Invalid selection. Using first installation.")
                        selection = 0
                    file_path = installations[selection][0]
                    print(f"Selected: {file_path}")
                except ValueError:
                    print("Invalid input. Using first installation found.")
                    file_path = installations[0][0]

            return file_path, old_signkey, new_signkey
    
    except FileNotFoundError:
        print(f"The JSON file {json_file_path} was not found.")
        raise
    except json.JSONDecodeError:
        print(f"Error parsing the JSON file {json_file_path}.")
        raise

def replace_signkey_in_file(file_path, old_signkey, new_signkey):
    if len(old_signkey) != len(new_signkey):
        raise ValueError("The new signkey must be the same length as the old signkey.")

    if old_signkey.startswith("0x"):
        old_signkey = old_signkey[2:]
    if new_signkey.startswith("0x"):
        new_signkey = new_signkey[2:]

    if not re.fullmatch(r'[0-9a-fA-F]+', old_signkey):
        raise ValueError("The old signkey is not valid.")
    if not re.fullmatch(r'[0-9a-fA-F]+', new_signkey):
        raise ValueError("The new signkey is not valid.")

    try:
        with open(file_path, 'rb') as file:
            content = file.read()

        old_signkey_bytes = bytes.fromhex(old_signkey)
        new_signkey_bytes = bytes.fromhex(new_signkey)

        if old_signkey_bytes not in content:
            print(f"The old signkey '{old_signkey}' was not found in the file.")
        else:
            print(f"The old signkey '{old_signkey}' was found. Replacing...")

            content = content.replace(old_signkey_bytes, new_signkey_bytes)

            with open(file_path, 'wb') as file:
                file.write(content)

            if old_signkey_bytes in content:
                print("Error: The old signkey is still present in the file.")
            else:
                print("Signkey successfully replaced.")
    
    except PermissionError:
        print("\nPermission denied! Try running the script as Administrator.")
        if platform.system() == "Windows":
            print("Relaunching with admin privileges...")
            run_as_admin()
        else:
            print("On Linux/macOS, try running with sudo.")
            raise
    except FileNotFoundError:
        print(f"The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    if platform.system() == "Windows" and not is_admin():
        print("\nThis operation requires administrator privileges on Windows.")
        print("Relaunching with admin rights...")
        run_as_admin()
        return

    print(r"""      ___.   .__          __                _________                       __                 
_____ \_ |__ |  |   _____/  |_  ____   ____ \_   ___ \____________    ____ |  | __ ___________ 
\__  \ | __ \|  | _/ __ \   __\/  _ \ /    \/    \  \/\_  __ \__  \ _/ ___\|  |/ // __ \_  __ \
 / __ \| \_\ \  |_\  ___/|  | (  <_> )   |  \     \____|  | \// __ \\  \___|    <\  ___/|  | \/
(____  /___  /____/\___  >__|  \____/|___|  /\______  /|__|  (____  /\___  >__|_ \\___  >__|   
     \/    \/          \/                 \/        \/            \/     \/     \/    \/    
   
          """)
    print("Made by devilAPI\nGitHub: https://github.com/devilAPI/abletonCracker/\n")

    config_file = 'config.json'

    try:
        file_path, old_signkey, new_signkey = load_config(config_file)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        input("Press Enter to exit...")
        return

    print("\nPatching executable...")
    try:
        replace_signkey_in_file(file_path, old_signkey, new_signkey)
        print("\nPatch completed successfully!")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"\nPatch failed: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
