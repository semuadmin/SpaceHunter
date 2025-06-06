"""
supplyship.py

This module contains the SupplyShip sprite class, inherited from the
Automaton parent class, which represents a supply ship which can be
summoned by the player via the Communications panel.

The SupplyShip class also 'owns' and controls the Armoury class.

The supply ship itself does nothing but come and go, but 'docking' with the
supply ship is a precondition to Armoury weapons trading.

Created on 5 Jul 2020

@author: steely_eyed_missile_man
"""

from random import randrange

import pygame as pg

from spacehunter.armoury import Armoury
from spacehunter.automaton import SEEK, Automaton
from spacehunter.colors import GREEN, RED

vec = pg.math.Vector2

MAX_SPEED = 3
MAX_VELR = 3
APPROACH_RADIUS = 150
SEEK_FORCE = 0.1
REFRESH_SHIELD = 0
DOCKING_PROXIMITY = 3


class SupplyShip(Automaton):
    """
    Supply Ship class
    """

    image = "supplyship.png"

    def __init__(self, app, **kwargs):
        """
        Constructor
        """

        self._app = app  # Pointer to main pygame application instance
        self.img = self._app.image_dict[self.image]
        parking_pos = vec(self._app.width / 2, self._app.height / 2)
        parking_pos.from_polar((self._app.width + 500, randrange(0, 360)))
        Automaton.__init__(self, app, self.img, parking_pos, **kwargs)

        # Initialise armoury
        self.armoury = Armoury(
            self._app,
            self._app._display_surf,
            (self._app.width / 2 - 220, self._app.height / 2 - 200),
        )

        self.docked_msg = False

    def summon(self):
        """
        Summon supply ship to player's position using the
        Automaton parent class's 'SEEK' instinct
        """

        if not self._app.doing_supply:
            self._app.doing_supply = True
            self.maxvel = 3
            self.instinct = SEEK
            self.seek_target = self._app.player

    def dock(self):
        """
        Dock with supply ship
        """

        if self.pos.distance_to(self._app.player.pos) > DOCKING_PROXIMITY:
            self._app.set_warning("MANOUEVRE INTO POSITION BEFORE DOCKING", RED)
            return
        if self._app.player.weapons_hot:
            self._app.set_warning("WEAPONS TO COLD BEFORE DOCKING", RED)
            return

        snd = self._app.sound_dict["dock.wav"]
        snd.play()
        self._app.set_warning("DOCKED WITH SUPPLY SHIP", GREEN)
        self._app.player.docked = True

    def undock(self):
        """
        Undock from supply ship
        """

        snd = self._app.sound_dict["dock.wav"]
        snd.play()
        self._app.set_warning("SUPPLY SHIP UNDOCKED", GREEN)
        self._app.player.docked = False
        self._app.doing_supply = False
        self.park()

    def park(self):
        """
        'Park' supply ship in random off-screen location
        """

        parking_pos = vec(self._app.width / 2, self._app.height / 2)
        parking_pos.from_polar((self._app.width + 500, randrange(0, 360)))
        self.instinct = SEEK
        self.seek_target = parking_pos

    def do_supplies(self):
        """
        Once docked with supply ship, get supplies from armoury
        """

        if self._app.player.docked:
            self.armoury.set_payload()  # Update armoury with player's current payload
            self._app.doing_armoury = True
        else:
            self._app.set_warning("DOCK WITH SUPPLY SHIP FIRST", RED)

    def _check_in_play(self):
        """
        Override this function to determine what happens if the actor is 'out of play'
        This may simply govern border behaviour, or it may be more sophisticated
        """

        if self._app.out_of_play(self.pos):
            self.kill()
