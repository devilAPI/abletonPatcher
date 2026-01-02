# abletonPatcher - What is this?

This is an open-source implementation of the R2R patch and `R2RLIVE.dll` of Ableton Live, written in Python.

Like `R2RLIVE.dll`, this script uses Team R2R's signing key only.

# Disclaimer

This script is not the result of reverse engineering Ableton Live, and the output of this script **will not** circumvent the protection on an **unmodified** copy of Ableton Live.

# Download Ableton Installers

You can download the Ableton Installers directly from Ableton's servers. I made a small HTML file to make this easier for you.

[StaticAbletonDownloader](https://devilapi.github.io/StaticAbletonDownloader)

# Compatibility

- Works on Windows and Linux (with wine)
- Should work for all Ableton Live Versions above Live 9 (9,10,11,12)
- Every Edition works too (Lite, Intro, Standard, Suite)

# Quickstart Guide

1. Find your Ableton HWID: Open Ableton, and press "Authorize Ableton offline". You will find your HWID.
2. Right click `quickstart.cmd` and select `Run as Administrator`.
3. When the script asks you if you want to edit the config file, select `y`.
4. You will only need to change the top 3 variables. Enter your HWID, the Live version and edition and **save the file (Ctrl+S)**
5. The script will now ask you if you want to run the patcher. Select `y`.
6. Select the installation of Ableton you want to patch
7. The script will now ask if you want to open the folder, where `Authorize.auz` is located. Select `y`
5. Run Ableton, drag the `Authorize.auz` file into the Activation window

#### Hooray, you're done!

# Command Line Arguments
| Parameter | Type | Description | Default/Config |
|-----------|------|-------------|----------------|
| `--undo` | flag | Revert the patch (swap signkeys and skip authorization file) | Uses config.json values |
| `--file_path` | string | Path to Ableton Live executable or "auto" for auto-detection | config.json: `file_path` |
| `--old_signkey` | string | Old signkey (hex string) | config.json: `old_signkey` |
| `--new_signkey` | string | New signkey (hex string) | config.json: `new_signkey` |
| `--hwid` | string | Hardware ID (24 hex chars or 6 groups of 4) | config.json: `hwid` |
| `--edition` | string | Ableton edition (Lite, Intro, Standard, Suite) | config.json: `edition` |
| `--version` | integer | Ableton version (e.g., 12) | config.json: `version` |
| `--authorize_file_output` | string | Output path for Authorize.auz or "auto" | config.json: `authorize_file_output` |
| `--config_file` | string | Path, where the config file is located. | `config.json` |
| `--help` | flag | Show help message | N/A |

# Troubleshooting
#### I don't have administrator on my PC.
1. Copy your Ableton executable to the same folder where patch_ableton.py is located.
2. In config.json, change your file path from "auto" to the new file path of your Ableton exe.
3. Retry
4. It should work now. Then copy your Ableton exe back to the folder you got it from.

# Support
I do offer support on Discord (https://discord.gg/akswvyUk) and on Reddit (@devilAPIOnReddit)

# Credits

The Implementation of the KeyGen was made by [rufoa](https://github.com/rufoa). Go leave a star on his Git page!
