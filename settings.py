"""Save and load game data (configuration, controls, highscores, jokes)."""
import json
import random
from typing import Any, List

import pygame

import resources
from consts import CONFIG_FILE, PUN_FILE, DEFAULT_SETTINGS, DEFAULT_KEYMAPPING

settings = DEFAULT_SETTINGS
keymapping = DEFAULT_KEYMAPPING
highscores = []  # Ordered by score descending and date ascending
jokes = []


# GETS ======================================================================
def get_setting(option: str) -> Any:
    """Return configuration parameter.

    Possible options are 'sound', 'music', 'classic'."""
    return settings[option]


def get_key(action: str) -> Any:
    """Return necessary keys for a certain action.

    Possible actions are 'grid', 'pause', 'accept', 'exit', 'direction',
    'up', 'down', 'left', 'right'. 'direction' returns a dictionary, the
    rest return an integer"""
    if action in keymapping:
        result = keymapping[action]
    elif action in keymapping['direction'].values():
        directions = {v: k for k, v in keymapping['direction'].items()}
        result = int(directions[action])
    return result


def get_joke() -> str:
    """Return a random pun."""
    return random.choice(jokes)


def lower_highscore() -> int:
    """Return lowest score in the top."""
    return highscores[-1]['score']


def get_highscores() -> List[dict]:
    """Return top highscores list."""
    return highscores


# SETS ======================================================================
def set_settings(option: str, value: Any):
    """Set  configuration parameter.

    Possible options are 'sound', 'music', 'classic'."""
    settings[option] = value


# I/O =======================================================================
def save_config():
    """Write current configuration to file."""
    print(f"Saving config to {CONFIG_FILE}...", end=" ")
    data = {}
    data['settings'] = settings
    data['keymapping'] = keymapping
    data['highscores'] = highscores
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=4)
    except EnvironmentError:
        print(f"Error: could't save config to file.")
    else:
        print("Done.")


def load_config():
    """Load configuration from file."""
    global settings
    global highscores

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as fp:
            config = json.load(fp)
    except EnvironmentError:
        # Create config file
        print(f"Error: could't load config from {CONFIG_FILE}.")
        save_config()
    else:
        # Load values from file
        settings = config['settings'].copy()
        highscores = config['highscores'].copy()
        keymapping['pause'] = config['keymapping']['pause']
        keymapping['grid'] = config['keymapping']['grid']
        keymapping['exit'] = config['keymapping']['exit']
        keymapping['accept'] = config['keymapping']['accept']
        keymapping['direction'] = {}
        for key, value in config['keymapping']['direction'].items():
            keymapping['direction'][int(key)] = value

        # Set volumes
        resources.set_volume(get_setting("sound"))
        pygame.mixer.music.set_volume(get_setting("music"))


def load_jokes():
    """Load snake puns."""
    global jokes

    try:
        with open(PUN_FILE, "r", encoding="utf8") as fp:
            data = json.load(fp)
    except EnvironmentError:
        print(f"Couldn't load data from {PUN_FILE}")
        jokes = ["There are no snakes in my boot :("]
    else:
        jokes = data['jokes'].copy()
