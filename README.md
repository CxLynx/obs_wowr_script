# OBS WoW Recording Script
My attempt at an OBS Plugin to start recordings based on World of Warcraft events.

# Installation
1) Ensure Python is installed.
2) In OBS Studio, under Tools > Scripts, in the `Python Settings` tab, update your 
Python Install Path to the location of your Python installation. If you do this correctly, it will say
something like "Loaded Python Version 3.12" below the path.
3) Modify the script with your parameters
   1) At the top of the scripts under the # Constants section, update the `LOG_DIR` entry to be the path
   to your World of Warcraft installation. The double backslashes `\\` are intended, use two backslashes for
   each backslash in the path. 
4) Add the script to your OBS Studio under Tools > Scripts in the `Scripts` tab. That's it!
5) You can view what the script is doing by clicking the `Script Log` button. The script also logs things
to your WoW Log directory in a `wowr_log.txt` file. 