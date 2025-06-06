"""
controllers.py

This module defines default joystick controller assignments, where these cannot be
read from a json config file in the user's home directory.

These were originally based on defaults assignments for the 8BitDo SN30 Pro+
controller on MacOS. Amend as necessary for your controller

Created on 10 Jun 2020

@author: steely_eyed_missile_man
"""

DEFAULT_CONFIG = {
    "JOYL_X": 0,
    "JOYL_Y": 1,
    "JOYR_X": 2,
    "JOYR_Y": 3,
    "JOY_L2": 4,
    "JOY_R2": 5,
    "HAT_UP": 11,
    "HAT_DOWN": 12,
    "HAT_LEFT": 13,
    "HAT_RIGHT": 14,
    "BTN_JOYL": 7,
    "BTN_JOYR": 8,
    "BTN_L1": 9,
    "BTN_R1": 10,
    "BTN_L2": "",
    "BTN_R2": "",
    "BTN_L3": "",
    "BTN_R3": "",
    "BTN_X": 3,
    "BTN_Y": 2,
    "BTN_A": 1,
    "BTN_B": 0,
    "BTN_SELECT": 4,
    "BTN_START": 5,
}
