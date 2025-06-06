"""
globals.py

This module contains global constants which defines overall game
characteristics and resource paths.

Created on 10 Jun 2020

@author: steely_eyed_missile_man
"""

from os import path
from pathlib import Path

HOME = Path.home()
CONFIGFILE = path.join(HOME, "spaceshooterconfig.json")

# Display resolution
WIDTH = 800
HEIGHT = 600
FULLSCREEN = True
PLAYER = 0
ENEMY = 1

# Sound FX
SNDVOL = 0.6  # Set to 0 to mute sound
MUSVOL = 0.4  # Set to 0 to mute music

# Font alignments
ALIGN_CENTER = 0
ALIGN_LEFT = 1
ALIGN_RIGHT = 2
ALIGN_BOTTOM = 4
ALIGN_MID = 5

# Asset folders
DIRNAME = path.dirname(__file__)
STATEFILE = path.join(DIRNAME, "..", "gamestate.json")
IMGDIR = path.join(DIRNAME, "images")
SNDDIR = path.join(DIRNAME, "sounds")
FONTDIR = path.join(DIRNAME, "fonts")

# Game states
NEWGAME = 0
PLAYING = 1
PAUSED = 2
GAMEOVER = 3

# Controller mode
KEYBOARD = 0
ONEAXISJOY = 1
TWOAXISJOY = 2

# Joystick axis sensitivities
JOY_X_SENS = 0.2
JOY_Y_SENS = 0.4
JOY_R_SENS = 0.05

# Game parameters
ENEMIES = True  # Turns enemy storms on or off
ASTEROIDS = True  # Turn asteroid storms on or off
ENEMY_SHOOTS = True  # Turn enemy shooting on or off
DEFAULT_USER = "myuser"
FPS = 60  # Frame rate
LEVELS = 5  # Number of game levels
LIVES = 3  # Default initial number of player lives
ASTSPEED = 6  # Max speed at which asteroids move
ASTSPEEDR = 50  # Max asteroid rotation speed
ASTMIN = 1000  # Minimum asteroid storm interval
ASTMAX = 5000  # Minimum asteroid storm interval
ASTSTORM = 10  # Initial number of asteroids in storm
ENEMYMIN = 1000  # Minimum enemy storm interval
ENEMYMAX = 5000  # Maximum enemy storm interval
ENEMYSTORM = 1  # Initial number of enemies in storm
NEW_LIFE_INT = 2000  # Pause when respawning new life
INPLAYRANGE = 3  # Multiple of screen width considered within 'in play' range
