import json
import re
import os
import sys
import ctypes
import platform
import subprocess

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Dummy:
        RESET = RED = WHITE = GREEN = LIGHTBLACK_EX = BRIGHT = ''
    Fore = Style = Dummy()

RED = Fore.RED + Style.BRIGHT
WHITE = Fore.WHITE + Style.BRIGHT
GREY = Fore.LIGHTBLACK_EX + Style.NORMAL
GREEN = Fore.GREEN + Style.BRIGHT
RESET = Style.RESET_ALL

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
                    print(RED + "\nNo Ableton Live installations found. Please specify the path manually." + RESET)
                    input(GREY + "Press Enter to exit..." + RESET)
                    sys.exit(1)

                print(WHITE + "\nFound Ableton installations:" + RESET)
                for i, (path, name) in enumerate(installations):
                    print(WHITE + f"{i+1}. " + WHITE + f"{name}" + GREY + f" at {path}" + RESET)

                try:
                    selection = int(input(WHITE + "\nSelect installation to patch: " + RED)) - 1
                    if selection < 0 or selection >= len(installations):
                        print(RED + "Invalid selection. Using first installation." + RESET)
                        selection = 0
                    file_path = installations[selection][0]
                    print(WHITE + f"Selected: {file_path}" + RESET)
                except ValueError:
                    print(RED + "Invalid input. Using first installation found." + RESET)
                    file_path = installations[0][0]

            return file_path, old_signkey, new_signkey
    
    except FileNotFoundError:
        print(RED + f"The JSON file {json_file_path} was not found." + RESET)
        raise
    except json.JSONDecodeError:
        print(RED + f"Error parsing the JSON file {json_file_path}." + RESET)
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
            print(RED + f"The old signkey was not found in the file." + RESET)
        else:
            print(WHITE + f"The old signkey was found. Replacing..." + RESET)

            content = content.replace(old_signkey_bytes, new_signkey_bytes)

            with open(file_path, 'wb') as file:
                file.write(content)

            if old_signkey_bytes in content:
                print(RED + "Error: The old signkey is still present in the file." + RESET)
            else:
                print(GREEN + "Signkey successfully replaced." + RESET)
    
    except PermissionError:
        print(RED + "\nPermission denied! Try running the script as Administrator." + RESET)
        if platform.system() == "Windows":
            print(GREY + "Relaunching with admin privileges..." + RESET)
            run_as_admin()
        else:
            print(GREY + "On Linux/macOS, try running with sudo." + RESET)
            raise
    except FileNotFoundError:
        print(RED + f"The file '{file_path}' was not found." + RESET)
    except Exception as e:
        print(RED + f"An error occurred: {e}" + RESET)

def main():
    if platform.system() == "Windows" and not is_admin():
        print(RED + "\nThis operation requires administrator privileges on Windows." + RESET)
        print(GREY + "Relaunching with admin rights..." + RESET)
        run_as_admin()
        return

    print(RED + r"""      ___.   .__          __                _________                       __                 
_____ \_ |__ |  |   _____/  |_  ____   ____ \_   ___ \____________    ____ |  | __ ___________ 
\__  \ | __ \|  | _/ __ \   __\/  _ \ /    \/    \  \/\_  __ \__  \ _/ ___\|  |/ // __ \_  __ \
 / __ \| \_\ \  |_\  ___/|  | (  <_> )   |  \     \____|  | \// __ \\  \___|    <\  ___/|  | \/
(____  /___  /____/\___  >__|  \____/|___|  /\______  /|__|  (____  /\___  >__|_ \\___  >__|   
     \/    \/          \/                 \/        \/            \/     \/     \/    \/    
   """ + RESET)
    print(WHITE + "Made by " + RED + "devilAPI" + RESET)
    print(WHITE + "GitHub: " + GREY + "https://github.com/devilAPI/abletonCracker/" + RESET + "\n")

    config_file = 'config.json'

    try:
        file_path, old_signkey, new_signkey = load_config(config_file)
    except Exception as e:
        print(RED + f"Error loading configuration: {e}" + RESET)
        input(GREY + "Press Enter to exit..." + RESET)
        return

    print(WHITE + "\nPatching executable..." + RESET)
    try:
        replace_signkey_in_file(file_path, old_signkey, new_signkey)
        print(WHITE + "\nPatch completed successfully!" + RESET)
        input(GREY + "Press Enter to exit..." + RESET)
    except Exception as e:
        print(RED + f"\nPatch failed: {e}" + RESET)
        input(GREY + "Press Enter to exit..." + RESET)

if __name__ == "__main__":
    main()