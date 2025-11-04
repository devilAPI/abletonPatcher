# abletonCracker - What is this?

This is an open-source implementation of the R2R Patch and `R2RLIVE.dll` of Ableton Live, written in Python 3.

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

# How to use

1. Install Python (3.12 upwards) at [python.org](https://www.python.org/downloads/)
2. Open your Terminal and run `python -m pip install cryptography` to install dependencies
3. Find your Ableton HWID, open Ableton, and press "Authorize Ableton offline". You will find your HWID.
4. Open `config.json` and change the variables to fit your Ableton Live installation.
5. Open your Ableton installation folder (for example: `C:\ProgramData\Ableton\Live 11 Suite\Program`)
6. Copy the Ableton executable (.exe file) (for example: `Ableton Live 11 Suite.exe`) to the same folder where you downloaded abletonCracker.
7. Run `patch_ableton.py`, your Ableton should be patched and the `Authorize.auz` file should generate.
8. Copy your Ableton executable back to your installation folder
9. Run Ableton, drag the `Authorize.auz` file into the Activation window

Hooray, you're done!

If there are any permission erros, its recommended to move the Ableton.exe into the same folder where `patch_ableton.py` is located.

# Credits

The Implementation of the KeyGen was made by [rufoa](https://github.com/rufoa). Go leave a star on his Git page!
