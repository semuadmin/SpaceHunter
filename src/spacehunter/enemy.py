"""
enemy.py

This module contains a series of 'Enemy' sprite classes inherited from the
Automaton parent class

Created on 26 Jun 2020

@author: steely_eyed_missile_man
"""

from random import randrange

import pygame as pg

from spacehunter.automaton import Automaton
from spacehunter.explosion import Explosion
from spacehunter.globals import ENEMY, ENEMY_SHOOTS
from spacehunter.weapons import *

vec = pg.math.Vector2

MAX_SPEED = 3
MAX_YAW = 5
APPROACH_RADIUS = 50
SEEK_FORCE = 0.1
FLEE_FORCE = 0.1
FLEE_DISTANCE = 20
APPROACH_ANGLE = 30
MIN_SHOOT_INT = 2000  # Minimum interval between shooting bursts
MAX_SHOOT_INT = 5000  # Maximum interval between shooting bursts
MIN_BURST_INT = 50  # Minimum length of burst of fire
MAX_BURST_INT = 500  # Maximum length of burst of fire
WPN_COOLOFF_INT = 3000  # Weapon junk check interval
WPN_COOLOFF_RATE = 10  # How quickly weapons_group cool down
REFRESH_AMMO = 5000  # Ammo auto-replenish interval (0 = no auto-replenish)
REFRESH_SHIELD = 0  # Shield auto-replenish interval (0 = no auto-replenish)
BOUNTY = 1000  # Player score for destroying enemy


class Enemy(Automaton):
    """
    This is an enemy bug class inherited from Automaton
    """

    image = "enemyBlue1.png"

    def __init__(self, app, pos, **kwargs):
        """
        Constructor
        """

        self._app = app  # Pointer to main pygame application instance
        self.img = self._app.image_dict[self.image]
        Automaton.__init__(self, app, self.img, pos, **kwargs)

        self._last_shooting = 0
        self._last_auto_fire = 0
        self._last_burst = 0
        self._shooting = False
        self.last_wpn_cool = 0
        self.desired_rot = 0
        self._last_shooting_int = MAX_SHOOT_INT
        self._burst_int = MAX_BURST_INT

        self._weapons = kwargs.get("weapons", [])
        self.add_weapon("Laser", Laser.capacity)
        self.add_weapon("Gatling", Gatling.capacity)
        self._sel_weapon = randrange(len(self._weapons))

    def update(self):
        """
        Update enemy
        """

        if ENEMY_SHOOTS and not self._shooting:
            self._start_shooting()

        if self._shooting:
            self._do_shooting()

        # Cool off any overheated weapons_group
        now = pg.time.get_ticks()
        if now - self.last_wpn_cool > WPN_COOLOFF_INT:
            self.last_wpn_cool = now
            for wpn in self._weapons:
                wpn["temp"] = wpn["temp"] - WPN_COOLOFF_RATE
                if wpn["temp"] < 0:
                    wpn["temp"] = 0

        super().update()

    def _do_events(self):
        """
        Respond to collisions with various objects
        """

        hits = pg.sprite.spritecollide(
            self, self._app.weapons_group, True, pg.sprite.collide_circle
        )
        for hit in hits:
            Explosion(self._app, self.pos, "sm")
            self.health -= hit.damage
            self._check_fatal_hit(hit)
            hit.kill()

        hits = pg.sprite.spritecollide(
            self, self._app.spacejunk_group, True, pg.sprite.collide_circle
        )
        for hit in hits:
            Explosion(self._app, self.pos, "sm")
            self.health -= hit.damage
            hit.disintegrate()

    def _start_shooting(self):
        """
        Start burst of automatic fire of random length
        """

        # Only start shooting if enemy is visible on screen
        if self._app.on_screen(self.pos):
            now = pg.time.get_ticks()
            if now - self._last_shooting > self._last_shooting_int:
                self._sel_weapon = randrange(len(self._weapons))
                self._burst_int = randrange(MIN_BURST_INT, MAX_BURST_INT)
                self._last_burst = now
                self._shooting = True

    def _do_shooting(self):
        """
        Do automatic fire burst
        """

        now = pg.time.get_ticks()
        if now - self._last_burst > self._burst_int:
            self._shooting = False
            self._last_shooting_int = randrange(MIN_SHOOT_INT, MAX_SHOOT_INT)
            self._last_shooting = now
        else:
            self.auto_shoot()

    def _check_fatal_hit(self, hit):
        """
        Check if a player weapon inflicted fatal damage. If it did,
        player gets a bonus. What can I say, it's a cruel world.
        """

        if self.health <= 0:
            Explosion(self._app, hit.rect.center, "lg")
            self._app.do_wreckage(hit.rect.center, self.vel)
            self._app.player.update_score(BOUNTY)
        else:
            self._app.player.update_score(hit.damage)

    def _check_in_play(self):
        """
        Override this function to determine what happens if the actor is 'out of play'
        This may simply govern border reaction, or it may be more sophisticated
        """

        if self._app.out_of_play(self.pos):
            self.kill()

    def _shoot(self):
        """
        Shoot using selected weapon class
        """

        if len(self._weapons) >= self._sel_weapon:
            wpn = self._weapons[self._sel_weapon]
            if wpn["wpn_class"] == "Empty":
                return False
            wpn_class = globals()[wpn["wpn_class"]]  # Instantiate class from name
            max_temp = wpn_class.max_temp
            ammo = wpn["ammo"]
            temp = wpn["temp"]
            if max_temp == 0 or temp < max_temp:  # Check weapon hasn't overheated
                if ammo > 0:
                    wpn = wpn_class(self._app, ENEMY, vec(self.pos), self.rot)
                    self._app.enemy_weapons_group.add(wpn)
                    ammo -= 1
                    temp += 1
                    self._weapons[self._sel_weapon]["ammo"] = ammo
                    self._weapons[self._sel_weapon]["temp"] = temp

    def auto_shoot(self):
        """
        Rapid auto fire where selected weapon class allows it
        """

        if len(self._weapons) >= self._sel_weapon:
            wpn = self._weapons[self._sel_weapon]
            wpn_class = globals()[wpn["wpn_class"]]

            if wpn_class.rate_of_fire > 1:
                now = pg.time.get_ticks()
                if now - self._last_auto_fire > int(60000 / wpn_class.rate_of_fire):
                    self._last_auto_fire = now
                    self._shoot()

    def add_weapon(self, wpn_class, ammo, temp=0):
        """
        Add weapon to payload
        """

        self._weapons.append({"wpn_class": wpn_class, "ammo": ammo, "temp": temp})

    def park(self):
        """
        'Park' enemy in random off-screen location
        """

        parking_pos = vec(self._app.width / 2, self._app.height / 2)
        parking_pos.from_polar((self._app.width + 500, randrange(0, 360)))
        self.instinct = SEEK
        self.seek_target = parking_pos
