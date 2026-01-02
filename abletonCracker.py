import json
import re
import os
import platform
import sys
import ctypes
import subprocess
import argparse
from random import randint
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import dsa
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.hazmat.primitives.hashes import SHA1

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Dummy:
        RESET = RED = WHITE = GREEN = LIGHTBLACK_EX = BRIGHT = ''
    Fore = Style = Dummy()

patcher_version = "v3.0.0"

RED = Fore.RED + Style.BRIGHT
WHITE = Fore.WHITE + Style.BRIGHT
GREY = Fore.LIGHTBLACK_EX + Style.NORMAL
GREEN = Fore.GREEN + Style.BRIGHT
YELLOW = Fore.YELLOW + Style.BRIGHT
PURPLE = Fore.MAGENTA + Style.BRIGHT
RESET = Style.RESET_ALL

os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def run_as_admin(undo=False):
    script = os.path.abspath(sys.argv[0])
    params = sys.argv[1:]
    if undo and "--undo" not in params:
        params.append("--undo")
    params = subprocess.list2cmdline(params)
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
    sys.exit(0)

def load_config(filename: str, args):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Use command line arguments if provided, otherwise use config file
        file_path = args.file_path if args.file_path else data.get("file_path")
        old_signkey = args.old_signkey if args.old_signkey else data.get("old_signkey")
        new_signkey = args.new_signkey if args.new_signkey else data.get("new_signkey")
        hwid = args.hwid if args.hwid else data.get('hwid', '').upper()
        edition = args.edition if args.edition else data.get('edition', 'Suite')
        version = args.version if args.version else data.get('version', 12)
        authorize_file_output = args.authorize_file_output if args.authorize_file_output else data.get('authorize_file_output', 'output/Authorize.auz')
        dsa_params = data.get('dsa_parameters')  # Keep DSA params in config only
        
        if args.undo:
            # For undo, swap the signkeys
            old_signkey, new_signkey = new_signkey, old_signkey
            
        if not file_path or not old_signkey or not new_signkey:
            raise ValueError("JSON file must contain 'file_path', 'old_signkey', and 'new_signkey'.")
        
        if len(hwid) == 24:
            hwid = "-".join(hwid[i:i+4] for i in range(0, 24, 4))
        assert re.fullmatch(r"([0-9A-F]{4}-){5}[0-9A-F]{4}", hwid), f"Expected hardware ID like 1111-1111-1111-1111-1111-1111, not {hwid}"
        
        if not dsa_params and not args.undo:
            raise ValueError("DSA parameters are missing in the config file.")
            
        return file_path, old_signkey, new_signkey, hwid, edition, version, authorize_file_output, dsa_params
    except FileNotFoundError:
        print(RED + f"The JSON file {filename} was not found." + RESET)
        raise
    except json.JSONDecodeError:
        print(RED + f"Error parsing the JSON file {filename}." + RESET)
        raise

def construct_key(dsa_params) -> dsa.DSAPrivateKey:
    p = int(dsa_params['p'], 16)
    q = int(dsa_params['q'], 16)
    g = int(dsa_params['g'], 16)
    y = int(dsa_params['y'], 16)
    x = int(dsa_params['x'], 16)
    params = dsa.DSAParameterNumbers(p, q, g)
    pub = dsa.DSAPublicNumbers(y, params)
    priv = dsa.DSAPrivateNumbers(x, pub)
    return priv.private_key(backend=default_backend())

def replace_signkey_in_file(file_path, old_signkey, new_signkey, undo: bool = False):
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
            if undo:
                print(RED + f"The old signkey was not found in the file." + RESET)
            else:
                if new_signkey_bytes in content:
                    print(YELLOW + "The new signkey is already present in the file. Ableton is already patched." + RESET)
                else:
                    print(RED + "Neither the old nor the new signkey was found in the file. You may be running an unsupported version or a different patch." + RESET)
        else:
            if undo:
                print(WHITE + f"The old signkey was found. Replacing..." + RESET)
            else:
                print(WHITE + "The old signkey was found. Replacing..." + RESET)
                
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
            run_as_admin(undo)
        else:
            print(GREY + "On Linux/macOS, try running with sudo." + RESET)
        raise
    except FileNotFoundError:
        print(RED + f"The file '{file_path}' was not found." + RESET)
        raise
    except Exception as e:
        print(RED + f"An error occurred: {e}" + RESET)
        raise

def sign(k: dsa.DSAPrivateKey, m: str) -> str:
    assert k.key_size == 1024
    sig = k.sign(m.encode(), SHA1())
    r, s = decode_dss_signature(sig)
    return "{:040X}{:040X}".format(r, s)

def fix_group_checksum(group_number: int, n: int) -> int:
    checksum = n >> 4 & 0xf ^ \
    n >> 5 & 0x8 ^ \
    n >> 9 & 0x7 ^ \
    n >> 11 & 0xe ^ \
    n >> 15 & 0x1 ^ \
    group_number
    return n & 0xfff0 | checksum

def overall_checksum(groups: list[int]) -> int:
    r = 0
    for i in range(20):
        g, digit = divmod(i, 4)
        v = groups[g] >> (digit * 8) & 0xff
        r ^= v << 8
        for _ in range(8):
            r <<= 1
            if r & 0x10000:
                r ^= 0x8005
    return r & 0xffff

def random_serial():
    """ 3xxc-xxxc-xxxc-xxxc-xxxc-dddd x is random c is a checksum over each group d is a checksum over all groups """
    groups = [randint(0x3000, 0x3fff), randint(0x0000, 0xffff), randint(0x0000, 0xffff), randint(0x0000, 0xffff), randint(0x0000, 0xffff)]
    for i in range(5):
        groups[i] = fix_group_checksum(i, groups[i])
    d = overall_checksum(groups)
    return "{:04X}-{:04X}-{:04X}-{:04X}-{:04X}-{:04X}".format(*groups, d)

def generate_single(k: dsa.DSAPrivateKey, id1: int, id2: int, hwid: str) -> str:
    f = "{},{:02X},{:02X},Standard,{}"
    serial = random_serial()
    msg = f.format(serial, id1, id2, hwid)
    sig = sign(k, msg)
    return f.format(serial, id1, id2, sig)

def generate_all(k: dsa.DSAPrivateKey, edition: str, version: int, hwid: str) -> str:
    yield generate_single(k, EDITIONS[edition], version << 4, hwid)
    for i in range(0x40, 0xff + 1):
        yield generate_single(k, i, 0x10, hwid)
    for i in range(0x8000, 0x80ff + 1):
        yield generate_single(k, i, 0x10, hwid)

EDITIONS = {
    "Lite": 4,
    "Intro": 3,
    "Standard": 0,
    "Suite": 2,
}

def get_user_config_dir():
    system = platform.system()
    if system == "Windows":
        return os.getenv('APPDATA')
    elif system == "Darwin":
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        return os.getenv('XDG_CONFIG_HOME', os.path.join(os.path.expanduser("~"), ".config"))

def find_installations():
    system = platform.system()
    installations = []
    if system == "Windows":
        base_dir = "C:\\ProgramData\\Ableton"
        if not os.path.exists(base_dir):
            return installations
        for entry in os.listdir(base_dir):
            if entry.startswith('.'):
                continue
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
            if entry.startswith('.'):
                continue
            if entry.endswith(".app") and "Ableton Live" in entry:
                app_path = os.path.join(base_dir, entry)
                exe_path = os.path.join(app_path, "Contents", "MacOS", "Live")
                if os.path.exists(exe_path):
                    name = entry.replace(".app", "")
                    installations.append((exe_path, name))

    installations.reverse()
    return installations

def find_installation_data():
    config_dir = get_user_config_dir()
    base_dir = os.path.join(config_dir, "Ableton")
    data_dirs = []
    if not os.path.exists(base_dir):
        return data_dirs
    for entry in os.listdir(base_dir):
        if entry.startswith('.'):  # Ignore folders starting with .
            continue
        entry_path = os.path.join(base_dir, entry)
        if os.path.isdir(entry_path) and "Live" in entry:
            data_dirs.append((entry_path, entry))
    
    # Reverse the list so newest versions are at the top
    data_dirs.reverse()
    return data_dirs

def open_folder(path):
    folder_path = os.path.dirname(path)
    if not os.path.exists(folder_path):
        print(RED + f"Folder does not exist: {folder_path}" + RESET)
        return False
        
    try:
        if platform.system() == "Windows":
            os.startfile(folder_path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", folder_path])
        else:  # Linux and other Unix-like
            subprocess.Popen(["xdg-open", folder_path])
        return True
    except Exception as e:
        print(RED + f"Failed to open folder: {e}" + RESET)
        return False

def main():
    # Set up command line argument parser
    parser = argparse.ArgumentParser(description='Ableton Live Patcher', add_help=False)
    parser.add_argument('--undo', action='store_true', help='Revert the patch (swap signkeys and skip authorization file)')
    parser.add_argument('--file_path', type=str, help='Path to Ableton Live executable (or "auto")')
    parser.add_argument('--old_signkey', type=str, help='Old signkey (hex string)')
    parser.add_argument('--new_signkey', type=str, help='New signkey (hex string)')
    parser.add_argument('--hwid', type=str, help='Hardware ID (24 hex chars or 6 groups of 4)')
    parser.add_argument('--edition', type=str, choices=['Lite', 'Intro', 'Standard', 'Suite'], help='Ableton edition')
    parser.add_argument('--version', type=int, help='Ableton version (e.g., 12)')
    parser.add_argument('--authorize_file_output', type=str, help='Output path for Authorize.auz (or "auto")')
    parser.add_argument('--help', action='store_true', help='Show this help message')
    parser.add_argument('--config_file', type=str, default='config.json', help='Path to config JSON file (default: config.json)'
)
    
    # Parse arguments
    args, unknown = parser.parse_known_args()
    
    # Show help if requested
    if args.help:
        print(WHITE + "Ableton Live Patcher " + RED + patcher_version + RESET)
        print(WHITE + "Usage: python patcher.py [OPTIONS]" + RESET)
        print("\nOptions:")
        print("  --undo                      Revert the patch (swap signkeys and skip authorization file)")
        print("  --file_path PATH            Path to Ableton Live executable or 'auto'")
        print("  --old_signkey HEX           Old signkey (hex string)")
        print("  --new_signkey HEX           New signkey (hex string)")
        print("  --hwid ID                   Hardware ID (24 hex chars or 6 groups of 4)")
        print("  --edition EDITION           Ableton edition (Lite, Intro, Standard, Suite)")
        print("  --version NUMBER            Ableton version (e.g., 12)")
        print("  --authorize_file_output PATH Output path for Authorize.auz or 'auto'")
        print("  --help                      Show this help message")
        print("\n" + YELLOW + "Note: Command line arguments override values in config.json" + RESET)
        return

    if platform.system() == "Windows" and not is_admin():
        print(RED + "\nThis operation requires administrator privileges on Windows." + RESET)
        print(GREY + "Relaunching with admin rights..." + RESET)
        run_as_admin(args.undo)
        return

    print(RED + r"""      ___.   .__          __                _________                       __                 
_____ \_ |__ |  |   _____/  |_  ____   ____ \_   ___ \____________    ____ |  | __ ___________ 
\__  \ | __ \|  | _/ __ \   __\/  _ \ /    \/    \  \/\_  __ \__  \ _/ ___\|  |/ // __ \_  __ \
 / __ \| \_\ \  |_\  ___/|  | (  <_> )   |  \     \____|  | \// __ \\  \___|    <\  ___/|  | \/
(____  /___  /____/\___  >__|  \____/|___|  /\______  /|__|  (____  /\___  >__|_ \\___  >__|   
     \/    \/          \/                 \/        \/            \/     \/     \/    \/    
   """ + RESET)
    print(WHITE + "Made by " + RED + "devilAPI" + RESET)
    print(WHITE + "Version: " + RED + patcher_version + RESET)
    print(WHITE + "GitHub: " + GREY + "https://github.com/devilAPI/abletonCracker/" + RESET + "\n")
    
    if args.undo:
        print(PURPLE + "UNDO MODE: Reverting patch and skipping authorization file generation." + RESET)

    print(YELLOW + "NOTE: Make sure Ableton Live is not running while patching." + RESET)

    config_file = args.config_file
    try:
        file_path, old_signkey, new_signkey, hwid, edition, version, authorize_file_output, dsa_params = load_config(config_file, args)
    except Exception as e:
        print(RED + f"Error loading configuration: {e}" + RESET)
        input(GREY + "Press Enter to exit..." + RESET)
        return

    if file_path.lower() == "auto":
        installations = find_installations()
        if not installations:
            print(RED + "\nNo Ableton Live installations found. Please specify the path manually." + RESET)
            input(GREY + "Press Enter to exit..." + RESET)
            return
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

    # Skip authorization file generation in undo mode
    if not args.undo:
        if authorize_file_output.lower() == "auto":
            data_dirs = find_installation_data()
            if not data_dirs:
                config_dir = get_user_config_dir()
                default_dir = os.path.join(config_dir, "Ableton", f"Live {version} {edition}")
                unlock_dir = os.path.join(default_dir, "Unlock")
                os.makedirs(unlock_dir, exist_ok=True)
                authorize_file_output = os.path.join(unlock_dir, "Authorize.auz")
                print(WHITE + f"\nUsing default authorization file location: " + WHITE + f"{authorize_file_output}" + RESET)
            else:
                print(WHITE + "\nFound Ableton data directories:" + RESET)
                for i, (path, name) in enumerate(data_dirs):
                    print(WHITE + f"{i+1}. " + WHITE + f"{name}" + GREY + f" at {path}" + RESET)
                try:
                    selection = int(input(WHITE + "\nSelect data directory: " + RESET)) - 1
                    if selection < 0 or selection >= len(data_dirs):
                        print(RED + "Invalid selection. Using first directory." + RESET)
                        selection = 0
                    unlock_dir = os.path.join(data_dirs[selection][0], "Unlock")
                    os.makedirs(unlock_dir, exist_ok=True)
                    authorize_file_output = os.path.join(unlock_dir, "Authorize.auz")
                    print(WHITE + f"Selected: " + GREY + f"{authorize_file_output}" + RESET)
                except ValueError:
                    print(RED + "Invalid input. Using first data directory found." + RESET)
                    unlock_dir = os.path.join(data_dirs[0][0], "Unlock")
                    os.makedirs(unlock_dir, exist_ok=True)
                    authorize_file_output = os.path.join(unlock_dir, "Authorize.auz")

        try:
            team_r2r_key = construct_key(dsa_params)
        except Exception as e:
            print(RED + f"Error constructing DSA key: {e}" + RESET)
            input(GREY + "Press Enter to exit..." + RESET)
            return

        print(WHITE + "\nGenerating authorization keys..." + RESET)
        try:
            lines = list(generate_all(team_r2r_key, edition, version, hwid))
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(authorize_file_output), exist_ok=True)
            with open(authorize_file_output, "w", newline="\n") as f:
                f.write("\n".join(lines))
            print("Authorization file created: " + WHITE + f"{authorize_file_output}" + RESET)
        except Exception as e:
            print(RED + f"Error generating authorization keys: {e}" + RESET)
            input(GREY + "Press Enter to exit..." + RESET)
            return

    print(WHITE + "\nPatching executable..." + RESET)
    try:
        replace_signkey_in_file(file_path, old_signkey, new_signkey, args.undo)
        print(GREEN + "\nPatch completed successfully!" + RESET)
        
        # Only show the authorization file instructions and folder opening in normal mode
        if not args.undo:
            print(GREEN + "SUCCESS! Your Ableton Live is now patched." + RESET)
            print(WHITE + "\nTo complete the activation:" + RESET)
            print(WHITE + "1. Start Ableton Live" + RESET)
            print(WHITE + "2. Simply drag and drop the " + YELLOW + "Authorize.auz" + WHITE + " file into the activation window" + RESET)
            print(YELLOW + "\nThat's it! No need to copy files manually." + RESET)
            
            try:
                response = input(WHITE + "\nDo you want to open the folder containing Authorize.auz? (y/N): " + RESET).strip().lower()
                if response in ['y', 'yes']:
                    if open_folder(authorize_file_output):
                        print(GREEN + "Folder opened successfully!" + RESET)
                    else:
                        print(RED + "Could not open the folder automatically." + RESET)
                        print(WHITE + "Please navigate to the folder manually. (usually in the same folder where the python file is located in the 'output' folder)" + RESET)
            except:
                pass  # If input fails, just continue
                
        input(GREY + "\nPress Enter to exit..." + RESET)
    except Exception as e:
        print(RED + f"\nPatch failed: {e}" + RESET)
        input(GREY + "Press Enter to exit..." + RESET)

if __name__ == "__main__":
    main()