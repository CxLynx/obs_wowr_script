import glob
import os
import datetime
import obspython as obs
from file_read_backwards import FileReadBackwards

# Constants
ENCOUNTER_START_TRIGGER = "ENCOUNTER_START"
CHALLENGE_MODE_START_TRIGGER = "CHALLENGE_MODE_START"
ENCOUNTER_END_TRIGGER = "ENCOUNTER_END"
CHALLENGE_MODE_END_TRIGGER = "CHALLENGE_MODE_END"
TIME_BACKSTOP = datetime.timedelta(seconds=10)
LOG_DIR = "C:\\Games\\World of Warcraft\\_retail_\\Logs\\"
TIMESTAMP_FORMAT = "%m/%d/%Y %H:%M:%S"

# Globals
log_file = ""
debug = True
in_encounter = False
in_dungeon = False


def update_combat_log_file():
  global log_file
  list_of_files = glob.glob(LOG_DIR + 'WoWCombatLog-*.txt')
  latest_file = max(list_of_files, key=os.path.getctime)
  log_file = latest_file
  log_with_message(f"Latest log file: {latest_file}")


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
  log_entry = f"{datetime.datetime.now()} - {message}\n"
  with open(LOG_DIR + "wowr_log.txt", "a") as file:
    file.write(log_entry)
  print(log_entry)


def read_combat_log():
  first_run_log()
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
      change_recording_state("start")
      return True

  if ENCOUNTER_END_TRIGGER in line and in_encounter:
    if not in_dungeon:
      log_with_message("Raid encounter end detected...ending raid encounter...")
      log_with_message(line)
      in_encounter = False
      log_with_message("Changing Recording state to OFF")
      change_recording_state("end")
      return True

  return False


def change_recording_state(mode: str):
  if mode == "start":
    if recording_active():
      log_with_message("Recording already active...skipping...")
    else:
      log_with_message("Attempting to start recording...")
      start_recording()
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


def script_description():
  return "Reads the World of Warcraft Combat Log to check for combat events to start and stop recording.\n\nBy Drathion"


obs.timer_add(read_combat_log, 3000)
