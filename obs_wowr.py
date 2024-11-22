import glob
import os
import datetime
import obspython as obs
from time import sleep
from file_read_backwards import FileReadBackwards

# Constants
ENCOUNTER_START_TRIGGER = "ENCOUNTER_START"
CHALLENGE_MODE_START_TRIGGER = "CHALLENGE_MODE_START"
ENCOUNTER_END_TRIGGER = "ENCOUNTER_END"
CHALLENGE_MODE_END_TRIGGER = "CHALLENGE_MODE_END"
TIME_BACKSTOP = datetime.timedelta(seconds=2)
LOG_DIR = "C:\\Program Files (x86)\\World of Warcraft\\_retail_\\Logs\\"
TIMESTAMP_FORMAT = "%m/%d/%Y %H:%M:%S"

# Globals
log_file = ""
debug = False
in_encounter = False
in_dungeon = False


def update_combat_log_file():
  global log_file
  list_of_files = glob.glob(LOG_DIR + 'WoWCombatLog-*.txt')
  latest_file = max(list_of_files, key=os.path.getctime)
  log_file = latest_file
  if debug: log_with_message(f"Latest log file: {latest_file}")


def get_line_timestamp(line: str) -> datetime.datetime:
  line_timestamp = line[:19].rstrip("-.")
  return datetime.datetime.strptime(line_timestamp, TIMESTAMP_FORMAT)


def is_not_past_backstop(log_time: datetime.datetime) -> bool:
  return log_time > (datetime.datetime.now() - TIME_BACKSTOP)


def first_run_log():
  log_with_message("Starting run")
  settings = [ENCOUNTER_START_TRIGGER, ENCOUNTER_END_TRIGGER, CHALLENGE_MODE_START_TRIGGER,
              CHALLENGE_MODE_END_TRIGGER, TIME_BACKSTOP, LOG_DIR, debug]
  log_with_message(f"Settings: {settings}")


def log_with_message(message: str):
  log_entry = f"{datetime.datetime.now()} - {message}"
  with open(LOG_DIR + "wowr_log.txt", "a") as file:
    file.write(log_entry)
  print(log_entry)


def read_combat_log():
  update_combat_log_file()
  with FileReadBackwards(log_file) as file:
    for line in file:
      line = line.replace('"', '\"')
      line_timestamp = get_line_timestamp(line)
      if is_not_past_backstop(line_timestamp):
        if change_combat_state(line):
          break
      else:
        if debug: log_with_message("Exceeded time backstop, stopping...")
        break


def change_combat_state(line: str) -> bool:
  global in_dungeon, in_encounter
  """These hopefully prevent few-second recordings on key start (noticed combat log tends to go like START->END->START on key start)
  Also implemented for raid with hunter/mage etc. boss resets in mind"""
  if ENCOUNTER_END_TRIGGER in line and not in_encounter and not in_dungeon:
    log_with_message("Detected ENCOUNTER_END, but recording wasn't active. Skipping older events")
    return True
  if CHALLENGE_MODE_END_TRIGGER in line and not in_dungeon:
    log_with_message("Detected CHALLENGE_MODE_END, but recording wasn't active. Skipping older events")
    return True

  if CHALLENGE_MODE_START_TRIGGER in line and not in_dungeon:
    log_with_message("CHALLENGE_MODE_START detected...starting M+ run...")
    log_with_message(line)
    in_dungeon = True
    log_with_message("Changing Recording state to ON")
    change_recording_state("start")
    return True

  if CHALLENGE_MODE_END_TRIGGER in line and in_dungeon:
    log_with_message("CHALLENGE_MODE_END detected...ending M+ run...")
    log_with_message(line)
    in_dungeon = False
    log_with_message("Changing Recording state to OFF")
    change_recording_state("end")
    return True

  if ENCOUNTER_START_TRIGGER in line and not in_encounter:
    if not in_dungeon:
      log_with_message("Raid encounter start detected...starting raid encounter...")
      log_with_message(line)
      in_encounter = True
      log_with_message("Changing Recording state to ON")
      if not recording_active:
        change_recording_state("start")
      elif recording_active:
        if recording_paused:
          change_recording_state("start")
          sleep(0.5) # IDK if this is needed, haven't tested without
        add_chapter()
      return True
  if ENCOUNTER_END_TRIGGER in line and in_encounter:
    if not in_dungeon:
      log_with_message("Raid encounter end detected...ending raid encounter...")
      log_with_message(line)
      in_encounter = False
      log_with_message("Changing Recording state to PAUSED")

      change_recording_state("pause")
      return True
  return False


def change_recording_state(mode: str):
  if mode == "start":
    if recording_active() and not recording_paused():
      log_with_message("Recording already active...skipping...")
    elif recording_active() and recording_paused():
      log_with_message("Attempting to unpause recording...")
      unpause_recording()
    else:
      log_with_message("Attempting to start recording...")
      start_recording()
  elif mode == "split":
    if mode == "split":
      if recording_active():
        log_with_message("Attempting to split recording...")
        split_recording()
      else:
        log_with_message("Recording not active... can't split")
  elif mode == "pause":
    if mode == "pause":
      if recording_active() and not recording_paused():
        log_with_message("Attempting to pause recording...")
        pause_recording()
  elif mode == "end":
    if recording_active():
      log_with_message("Attempting to stop recording...")
      stop_recording()
    else:
      log_with_message("Recording already stopped...skipping")


def write_debug_log_file(log_entry: str):
  log_with_message(log_entry)


def recording_active() -> bool:
  return obs.obs_frontend_recording_active()

def recording_paused() -> bool:
  return obs.obs_frontend_recording_paused()


def start_recording():
  """Starts recording if recording is not active"""
  if not recording_active():
    log_with_message("Recording starting...")
    try:
      obs.obs_frontend_recording_start()
    except Exception as e:
      log_with_message(f"Recording failed to start. {e}")
    else:
      log_with_message("Recording started...")

def stop_recording():
  """Stops recording if recording is active"""
  if recording_active():
    log_with_message("Recording stopping...")
    try:
      obs.obs_frontend_recording_stop()
    except Exception as e:
      log_with_message(f"Recording failed to stop. {e}")
    else:
      log_with_message("Recording stopped...")

def split_recording():
  """Splits currently active recording into another file"""
  if recording_active() and not recording_paused():
    log_with_message("Splitting recording...")
    try:
      obs.obs_frontend_recording_split_file()
    except Exception as e:
      log_with_message(f"Failed to split recording. {e}")
    else:
      log_with_message("Recording split...")

def add_chapter():
  """Adds a chapter marker to the recording, requires recording to 'Hybrid MP4' and OBS Studio 31"""
  if recording_active() and not recording_paused():
    log_with_message("Adding a new chapter...")
    try:
      obs.obs_frontend_recording_add_chapter(None)
    except Exception as e:
      log_with_message(f"Failed to add chapter. {e}")
    else:
      log_with_message("Chapter added...")
  elif recording_paused():
    log_with_message("!!! add_chapter was called but the recording is still paused !!!")

def pause_recording():
  """Pauses the recording if it's active"""
  if recording_active() and not recording_paused():
    log_with_message("Pausing recording")
    try:
      obs.obs_frontend_recording_pause(True)
    except Exception as e:
      log_with_message(f"Failed to pause recording. {e}")
    else:
      log_with_message("Recording paused...")

def unpause_recording():
  """Unpauses the recording if it's active and paused"""
  if recording_active() and recording_paused():
    log_with_message("Unpausing recording")
    try:
      obs.obs_frontend_recording_pause(False)
    except Exception as e:
      log_with_message(f"Failed to unpause recording. {e}")
    else:
      log_with_message("Recording unpaused...")


def script_description():
  return "Reads the World of Warcraft Combat Log to check for combat events to start and stop recording.\n\nBy Drathion"

def script_load(settings):
  first_run_log()

obs.timer_add(read_combat_log, 1000)