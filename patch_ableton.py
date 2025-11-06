import json
import re
import os
import platform
import sys
import ctypes
import subprocess
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

def load_config(filename: str, undo: bool = False):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        file_path = data.get("file_path")
        
        if undo:
            # For undo, swap the signkeys
            old_signkey = data.get("new_signkey")
            new_signkey = data.get("old_signkey")
        else:
            old_signkey = data.get("old_signkey")
            new_signkey = data.get("new_signkey")
            
        hwid = data.get('hwid', '').upper()
        edition = data.get('edition', 'Suite')
        version = data.get('version', 12)
        authorize_file_output = data.get('authorize_file_output', 'Authorize.auz')
        dsa_params = data.get('dsa_parameters')
        
        if not file_path or not old_signkey or not new_signkey:
            raise ValueError("JSON file must contain 'file_path', 'old_signkey', and 'new_signkey'.")
        
        if len(hwid) == 24:
            hwid = "-".join(hwid[i:i+4] for i in range(0, 24, 4))
        assert re.fullmatch(r"([0-9A-F]{4}-){5}[0-9A-F]{4}", hwid), f"Expected hardware ID like 1111-1111-1111-1111-1111-1111, not {hwid}"
        
        if not dsa_params and not undo:
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
    """P1363 format sig over m as a string of hex digits"""
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

def main():
    # Check for undo flag at the very beginning
    undo = "--undo" in sys.argv

    if platform.system() == "Windows" and not is_admin():
        print(RED + "\nThis operation requires administrator privileges on Windows." + RESET)
        print(GREY + "Relaunching with admin rights..." + RESET)
        run_as_admin(undo)
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
    
    if undo:
        print(PURPLE + "UNDO MODE: Reverting patch and skipping authorization file generation." + RESET)

    print(YELLOW + "NOTE: Make sure Ableton Live is not running while patching." + RESET)

    config_file = 'config.json'
    try:
        file_path, old_signkey, new_signkey, hwid, edition, version, authorize_file_output, dsa_params = load_config(config_file, undo)
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
    if not undo:
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
            with open(authorize_file_output, "w", newline="\n") as f:
                f.write("\n".join(lines))
            print("Authorization file created: " + WHITE + f"{authorize_file_output}" + RESET)
        except Exception as e:
            print(RED + f"Error generating authorization keys: {e}" + RESET)
            input(GREY + "Press Enter to exit..." + RESET)
            return

    print(WHITE + "\nPatching executable..." + RESET)
    try:
        replace_signkey_in_file(file_path, old_signkey, new_signkey, undo)
        print(WHITE + "\nPatch completed successfully!" + RESET)
        input(GREY + "Press Enter to exit..." + RESET)
    except Exception as e:
        print(RED + f"\nPatch failed: {e}" + RESET)
        input(GREY + "Press Enter to exit..." + RESET)

if __name__ == "__main__":
    main()