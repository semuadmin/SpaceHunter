"""
weapon.py

This module contains an 'abstract' weapons parent sprite class.

All weapons should inherit from this class and define the following
minimum set of class variables governing weapon character:

    image - the sprite image of the weapon
    sound - the sound the weapon makes when fired (optional)
    wpn_cost - the 'cost' of the weapon in score points
    ammo_cost - the 'cost' of each round of ammunition in score points
    notes - string describing any special characteristics of the weapon
    damage - how much damage each round does (i.e. deduction from shield)
    capacity - how many rounds can be carried in each weapons bay
    auto_replenish - whether ammunition auto-replenishes in background
    rate_of_fire - >1 = rounds per minute; 1 = single shot only
    max_temp - 'temperature' limit before weapon over-heats; 0 = no over-heating

Add the weapon class name to the Armoury.WPN_CLASSES class constant to make
the weapon available for trading.

Created on 10 Jun 2020

@author: steely_eyed_missile_man
"""

import pygame as pg

from spacehunter.automaton import Automaton
from spacehunter.globals import PLAYER

vec = pg.math.Vector2


class Weapon(Automaton):
    """
    Weapon class
    """

    def __init__(self, app, source, pos, **kwargs):
        img = app.image_dict[self.image]
        self.source = source
        if hasattr(self, "sound"):
            snd = app.sound_dict[self.sound]
            snd.play()
        Automaton.__init__(self, app, img, pos, **kwargs)

    def _do_events(self):
        """
        Handle collisions with passive objects
        (active object collisions should be handled by the
        active object class i.e. Player or Enemy)
        """

        hits = pg.sprite.spritecollide(
            self, self._app.spacejunk_group, True, pg.sprite.collide_circle
        )
        for hit in hits:
            self.health -= hit.damage
            # If Player fired weapon that hit asteroid, they get points
            if self.source == PLAYER:
                self._app.player.update_score(hit.damage)
            hit.disintegrate()

    def _check_in_play(self):
        """
        Kill weapon if out of play
        """

        if self._app.out_of_play(self.pos):
            self.kill()
