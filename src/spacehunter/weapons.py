"""
weapons.py

This module contains a series of weapon sprite definitions inherited
from the Weapon parent class (which is in turn inherited from the
common Automaton class).

Simple changes to weapon characteristics can be made by a amending
the class constants e.g. max_speed, capacity, rate_of_fire or damage.

More complex behaviour can be implemented by overriding the relevant
Weapon public base methods e.g. update().

Created on 10 Jun 2020

@author: steely_eyed_missile_man
"""

import pygame as pg

from spacehunter.automaton import SEEK
from spacehunter.weapon import Weapon

vec = pg.math.Vector2


class Empty(Weapon):
    """
    Empty weapon slot
    """

    wpn_cost = 0
    ammo_cost = 0
    notes = ""
    damage = 0
    capacity = 100
    auto_replenish = 0
    rate_of_fire = 0
    max_temp = 0

    image = "cold.png"

    def __init__(self, app, source, pos, rot=0):
        Weapon.__init__(self, app, source, pos, rot=rot, radius=0)


class Laser(Weapon):
    """
    Laser sprite class
    """

    wpn_cost = 1000
    ammo_cost = 30
    notes = (
        "Very high velocity. High rate of fire, but can over-heat"
        + " on long bursts. Automatically recharges in background."
    )
    damage = 10
    capacity = 100
    auto_replenish = 5
    rate_of_fire = 600
    max_temp = 30

    image = "laserRed01.png"
    sound = "laser.wav"

    def __init__(self, app, source, pos, rot=0):
        vel = vec(0, -30).rotate(rot * -1)
        Weapon.__init__(
            self, app, source, pos, vel=vel, rot=rot, maxvel=30, radius=3, health=1
        )


class UltraLaser(Weapon):
    """
    Laser sprite class
    """

    wpn_cost = 4000
    ammo_cost = 60
    notes = "Double the damage of a normal laser. Takes slightly longer to recharge"
    damage = 20
    capacity = 100
    auto_replenish = 4
    rate_of_fire = 600
    max_temp = 40

    image = "laserGreen10.png"
    sound = "laser.wav"

    def __init__(self, app, source, pos, rot=0):
        vel = vec(0, -30).rotate(rot * -1)
        Weapon.__init__(
            self, app, source, pos, vel=vel, rot=rot, maxvel=30, radius=3, health=1
        )


class Gatling(Weapon):
    """
    Gatling rail gun sprite class
    Every 10th round will be a 'tracer'
    """

    TRACER = 0
    BULLET = 1

    wpn_cost = 5000
    ammo_cost = 50
    notes = "Very high rate of fire, but will over-heat on long bursts. Watch your ammo level!"
    damage = 30
    capacity = 300
    auto_replenish = 0
    rate_of_fire = 1500
    max_temp = 50

    image = "gatling.png"
    tracer = "tracer.png"
    sound = "gatling.wav"

    def __init__(self, app, source, pos, rot=0):
        # Every 10th round will be a 'tracer' bullet
        app.round_type = (app.round_type + 1) % 10
        self.image = self.tracer if app.round_type == 0 else self.image
        vel = vec(0, -15).rotate(rot * -1)
        Weapon.__init__(
            self, app, source, pos, vel=vel, rot=rot, maxvel=15, radius=3, health=3
        )


class Missile(Weapon):
    """
    Missile sprite class
    """

    wpn_cost = 10000
    ammo_cost = 1500
    notes = "Not guided - line of sight only."
    damage = 100
    capacity = 80
    auto_replenish = 2
    rate_of_fire = 1
    max_temp = 0

    image = "missile.png"
    sound = "missile.wav"

    def __init__(self, app, source, pos, rot=0):
        """
        Constructor
        """

        vel = vec(0, -3).rotate(rot * -1)
        acc = vec(0, -0.1).rotate(rot * -1)
        Weapon.__init__(
            self, app, source, pos, vel=vel, rot=rot, acc=acc, maxvel=20, radius=6
        )


class Sidewinder(Weapon):
    """
    Guided Missile sprite class. Will find and actively track the nearest
    target, which can be position vector, an individual sprite or a sprite group
    """

    wpn_cost = 5000
    ammo_cost = 50
    notes = "Will automatically find and track the closest enemy targets."
    capacity = 100
    auto_replenish = 0
    damage = 100
    rate_of_fire = 1
    max_temp = 0

    image = "sidewinder.png"
    sound = "missile.wav"

    # These constants govern missile 'agility'
    APPROACH_RADIUS = 5
    MAX_FORCE = 0.3

    def __init__(self, app, source, pos, rot):
        """
        Constructor
        """

        vel = vec(0, -3).rotate(rot * -1)
        acc = vec(0, -0.1).rotate(rot * -1)
        Weapon.__init__(
            self,
            app,
            source,
            pos,
            vel=vel,
            rot=rot,
            maxvel=30,
            acc=acc,
            radius=10,
            seek_target=app.enemies_group,
        )

        self.launch_time = pg.time.get_ticks()

    def update(self):
        # Simulate guided missile 'target acquisition' delay
        now = pg.time.get_ticks()
        if now - self.launch_time > 300:
            self.instinct = SEEK
        super().update()


class Mine(Weapon):
    """
    Mine sprite class
    """

    wpn_cost = 15000
    ammo_cost = 2000
    notes = "Kill your velocity before laying to avoid drift."
    damage = 100
    capacity = 5
    auto_replenish = 0
    rate_of_fire = 1
    max_temp = 0

    image = "mine.png"
    sound = "minelay.wav"

    def __init__(self, app, source, pos, rot=0):
        """
        Constructor
        """

        vel = vec(app.player.vel)
        Weapon.__init__(self, app, source, pos, vel=vel, rot=rot, maxvel=99, radius=6)
