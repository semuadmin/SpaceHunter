"""
player.py

This module contains the main Player class. In single player mode, only
one of these should ever be instantiated.

Created on 10 Jun 2020

@author: steely_eyed_missile_man
"""

from copy import deepcopy

import pygame as pg

from spacehunter.colors import BLUE, CYAN, GREEN, RED
from spacehunter.explosion import Explosion
from spacehunter.globals import (
    JOY_R_SENS,
    JOY_X_SENS,
    JOY_Y_SENS,
    LIVES,
    NEW_LIFE_INT,
    PLAYER,
)
from spacehunter.spacejunk import Asteroid
from spacehunter.weapons import *

vec = pg.math.Vector2

# Player dynamics
LIMIT_SPEED = True  # Whether to limit speed
MAX_SPEED = 10  # Max speed at which player can move forwards
MAX_REVERSE = 5  # Max speed at which player can move backwards
MAX_SIDEWAYS = 5  # Max speed at which player can move sideways
MIN_SPEED = 0.1  # Min speed at which player can move in any direction
MAX_YAW = 3  # Max speed at which player rotates (yaws)
MIN_YAW = 0  # Min speed at which player rotates (yaws)
MAX_ACCEL = 1  # Max player acceleration
INERTIAL_DAMPING = True  # Turn inertial damping on or off
VEL_DAMPING = 1  # Strength of inertial damping for velocity
YAW_DAMPING = 5  # Strength of inertial damping for rotation

MAX_SHIELD = 100
MAX_WEAPONS = 5  # Max number of weapon classes held in payload
WPN_COOLOFF_INT = 3000  # Weapon temperature check interval
WPN_COOLOFF_RATE = 10  # How quickly weapons_group cool down
REFRESH_AMMO = 5000  # Ammo auto-replenish interval (0 = no auto-replenish)
REFRESH_SHIELD = 0  # Shield auto-replenish interval (0 = no auto-replenish)


class Player(pg.sprite.Sprite):
    """
    Player sprite class
    """

    image = "player.png"
    icon = "player_icon.png"
    death_sound = "rumble1.ogg"

    def __init__(
        self,
        app,
        pos,
        rot=0,
        level=0,
        score=0,
        shield=MAX_SHIELD,
        lives=LIVES,
        weapons=None,
    ):
        self._app = app  # Pointer to main application class
        pg.sprite.Sprite.__init__(self)

        self.image_orig = self._app.image_dict[self.image]
        self.image = self.image_orig.copy()
        self.rect = self.image.get_rect()

        self.pos = pos
        self.rot = rot
        self.vel = vec(0, 0)
        self.acc = vec(0, 0)
        self.velr = 0
        self.accr = 0
        self.rect.center = self.pos
        self.radius = 20
        self.level = level
        self.lives = lives
        self.score = score
        self.shield = shield
        self._hidden = False
        self._hide_timer = 0
        self._last_shot = 0
        self._last_update = 0
        self._last_damping = 0
        self._last_ammo_refresh = 0
        self._last_shield_refresh = 0
        self._last_auto_fire = 0
        self._last_new_life = 0
        self._auto_fire_rnds = 0
        self.last_wpn_cool = 0
        self.docked = False
        self.weapons_hot = False

        # Initialize weapons payload
        self._weapons = []
        if weapons is None:
            self.add_weapon("Empty", 0)
            self.add_weapon("Laser", Laser.capacity)
        else:
            for wpn in weapons:
                self.add_weapon(wpn["wpn_class"], wpn["ammo"])
        self._sel_weapon = 0

    def update(self):
        """
        Update player sprite
        """

        # Hide temporarily whilst respawning
        now = pg.time.get_ticks()
        if self._hidden and now - self._hide_timer > NEW_LIFE_INT:
            self._hide_timer = now
            self._hidden = False
            self.pos = (
                self._app.width / 2 - self.rect.width / 2,
                self._app.height - self.rect.height,
            )

        # Update velocity vectors
        self.vel += self.acc
        self.velr += self.accr
        if LIMIT_SPEED:
            # Limit speed relative to player orientation
            rvel = self.vel.rotate(-self.rot)
            if rvel.y < -MAX_SPEED:
                rvel.y = -MAX_SPEED
                self.vel = rvel.rotate(self.rot)
            if rvel.y > MAX_REVERSE:
                rvel.y = MAX_REVERSE
                self.vel = rvel.rotate(self.rot)
            if abs(rvel.x) > MAX_SIDEWAYS:
                rvel.x = MAX_SIDEWAYS if rvel.x > 0 else -MAX_SIDEWAYS
                self.vel = rvel.rotate(self.rot)
        if abs(self.velr) > MAX_YAW:
            if self.velr < 0:
                self.velr = -MAX_YAW
            else:
                self.velr = MAX_YAW

        # Update position and orientation
        self.rotate()
        self.pos += self.vel
        self.rot = (self.rot - self.velr) % 360
        self.rect.center = self.pos

        # Do inertial damping
        if INERTIAL_DAMPING:
            self._inertial_damping()

        # Do any interval-based resource replenishment
        if REFRESH_AMMO:
            self.recharge_ammo()
        if REFRESH_SHIELD:
            self.recharge_shield()

        # Cool off any overheated weapons
        now = pg.time.get_ticks()
        if now - self.last_wpn_cool > WPN_COOLOFF_INT:
            self.last_wpn_cool = now
            for wpn in self._weapons:
                wpn["temp"] = wpn["temp"] - WPN_COOLOFF_RATE
                if wpn["temp"] < 0:
                    wpn["temp"] = 0

        self._do_events()
        self._check_in_play()
        self._check_health()

    def _do_events(self):
        """
        Respond to collisions with various objects
        """

        # Check if enemy weapon hit the player
        hits = pg.sprite.spritecollide(
            self, self._app.enemy_weapons_group, True, pg.sprite.collide_circle
        )
        for hit in hits:
            Explosion(self._app, hit.pos, "sm")
            self.shield -= hit.damage

        # Check if spacejunk hit the player
        hits = pg.sprite.spritecollide(
            self, self._app.spacejunk_group, True, pg.sprite.collide_circle
        )
        for hit in hits:
            if hit.radius > 3:  # Ignore very small objects
                Explosion(self._app, hit.pos, "sm")
                self.shield -= hit.damage
                if isinstance(hit, Asteroid):
                    hit.disintegrate()

        # Check if wreckage hit the player
        hits = pg.sprite.spritecollide(
            self, self._app.wreckage_group, True, pg.sprite.collide_circle
        )
        for hit in hits:
            if hit.radius > 3:  # Ignore very small objects
                Explosion(self._app, hit.pos, "sm")
                self.shield -= hit.damage

    def _check_health(self):
        """
        Check health (shield state)
        """

        if self.shield <= 0:
            Explosion(self._app, self.rect.center, "death")
            self._app.sound_dict[self.death_sound].play()
            if self.lives > 0:
                self._get_new_life()

        # If no more lives, that's all folks
        if self.lives <= 0:
            self._app.on_gameover()

    def _get_new_life(self):
        """
        Respawn new life
        """

        self.hide()  # Hide sprite while respawning
        self.lives -= 1
        if self.lives > 0:
            self._app.set_warning(
                str(self.lives)
                + (" LIVES" if self.lives > 1 else " LIFE")
                + " REMAINING",
                BLUE,
            )
        self._app.on_new_life()
        self.shield = MAX_SHIELD

    def _check_in_play(self):
        """
        Keep sprite within visible display boundaries
        """

        if self._hidden:
            return
        if self.rect.right > self._app.width:
            self.vel.x = 0
            self.pos.x = self._app.width - self.rect.width / 2
        if self.rect.left < 0:
            self.vel.x = 0
            self.pos.x = self.rect.width / 2
        if self.rect.bottom > self._app.height:
            self.vel.y = 0
            self.pos.y = self._app.height - self.rect.height / 2
        if self.rect.top < 0:
            self.vel.y = 0
            self.pos.y = self.rect.height / 2

    def accelerate(self, **kwargs):
        """
        Set player acceleration RELATIVE TO player orientation (rotation).
        Takes up to 3 keyword parameters:
            thrust - acceleration in longitudinal (forward/backward) axis
            sideways - acceleration in perpendicular (sideways) axis
            yaw = acceleration in rotational axis
        """

        # Don't allow movement if player docked with supply ship
        if self.docked:
            self._app.set_warning("DOCKED", RED)
            self.vel = vec(0, 0)
            self.velr = 0
            self.acc = vec(0, 0)
            self.accr = 0
            return

        if "thrust" in kwargs:
            thrust = kwargs["thrust"] * JOY_Y_SENS
        else:
            thrust = 0
        if "sideways" in kwargs:
            sideways = kwargs["sideways"] * JOY_X_SENS
        else:
            sideways = 0
        if "yaw" in kwargs:
            yaw = kwargs["yaw"] * JOY_R_SENS
        else:
            yaw = 0

        # Make acceleration relative to player orientation (rotation)
        self.acc = vec(sideways, thrust).rotate(-self.rot)
        self.accr = yaw

    def rotate(self):
        """
        Rotate (yaw) player
        """

        new_image = pg.transform.rotate(self.image_orig, self.rot)
        old_center = self.rect.center
        self.image = new_image
        self.rect = self.image.get_rect()
        self.rect.center = old_center

    def _inertial_damping(self):
        """
        Gradually decrease residual velocities to zero in the absence
        of an acceleration force
        """

        if self.acc.length() == 0:
            self.vel /= 1 + VEL_DAMPING / 100
        if self.accr == 0:
            self.velr /= 1 + YAW_DAMPING / 100
        if self.vel.length() < MIN_SPEED:
            self.vel.update(0, 0)
        if abs(self.velr) < MIN_YAW:
            self.velr = 0

    def hide(self):
        """
        Hide the player temporarily while respawning new life
        """

        self._hidden = True
        self._hide_timer = pg.time.get_ticks()
        self.pos = (self._app.width / 2, self._app.height + 200)
        self.vel.update(0, 0)
        self.acc.update(0, 0)
        self.velr = 0
        self.accr = 0
        self.rot = 0

    def shoot(self):
        """
        Shoot using selected weapon class
        Returns True if weapon fired, else False
        """

        if len(self._weapons) >= self._sel_weapon:
            wpn = self._weapons[self._sel_weapon]
            if wpn["wpn_class"] == "Empty":
                return False
            wpn_class = globals()[wpn["wpn_class"]]
            max_temp = wpn_class.max_temp
            ammo = wpn["ammo"]
            temp = wpn["temp"]
            if max_temp == 0 or temp < max_temp:  # Check weapon hasn't overheated
                if ammo > 0:
                    wpn = wpn_class(self._app, PLAYER, vec(self.pos), self.rot)
                    self._app.weapons_group.add(wpn)
                    ammo -= 1
                    temp += 1
                    self._weapons[self._sel_weapon]["ammo"] = ammo
                    self._weapons[self._sel_weapon]["temp"] = temp
                    return True
                else:
                    r_msg = " - WAIT FOR RECHARGE" if wpn_class.auto_replenish else ""
                    self._app.set_warning("OUT OF AMMUNITION" + r_msg, RED)
            else:
                self._app.set_warning("WEAPON OVERHEATED", RED)

        return False

    def auto_shoot(self):
        """
        Rapid auto fire where selected weapon class allows it
        Returns True if weapon fired, else False
        """

        if len(self._weapons) >= self._sel_weapon:
            wpn = self._weapons[self._sel_weapon]
            wpn_class = globals()[wpn["wpn_class"]]

            if wpn_class.rate_of_fire > 1:
                now = pg.time.get_ticks()
                if now - self._last_auto_fire > int(60000 / wpn_class.rate_of_fire):
                    self._last_auto_fire = now
                    self.shoot()
                    return True

        return False

    def add_weapon(self, wpn_class, ammo, temp=0):
        """
        Add weapon to payload
        """

        if len(self._weapons) >= MAX_WEAPONS:
            return False

        self._weapons.append({"wpn_class": wpn_class, "ammo": ammo, "temp": temp})
        return True

    def cycle_weapon(self):
        """
        Cycle through available weapons
        """

        # Don't allow weapon cycling if player docked
        if self.docked:
            return

        self._sel_weapon = (self._sel_weapon + 1) % len(self._weapons)
        wpn_class = self._weapons[self._sel_weapon]["wpn_class"]
        if wpn_class == "Empty":
            self.weapons_hot = False
            self._app.set_warning("WEAPONS COLD", CYAN)
        else:
            self.weapons_hot = True
            msg = wpn_class + " Selected"
            self._app.set_warning(msg, GREEN)

    def get_ammo(self):
        """
        Get selected weapon class and ammo level
        """

        wpn = self._weapons[self._sel_weapon]
        return wpn["wpn_class"], wpn["ammo"]

    def get_payload(self):
        """
        Get weapons payload
        """

        wpns = deepcopy(self._weapons)  # Return a copy, not a reference
        return wpns, self._sel_weapon

    def update_score(self, val):
        """
        Set player score
        """

        self.score += val

    def update_payload(self, payload):
        """
        Update weapons payload
        """

        self._weapons = deepcopy(payload)  # Use a copy, not a reference

    def recharge_ammo(self):
        """
        Replenish ammo automatically after specified time interval
        """

        now = pg.time.get_ticks()
        if now - self._last_ammo_refresh > REFRESH_AMMO:
            self._last_ammo_refresh = now
            for count, wpn in enumerate(self._weapons):
                wpn_class = globals()[wpn["wpn_class"]]
                ammo = wpn["ammo"]
                if wpn_class.auto_replenish:
                    ammo += wpn_class.auto_replenish
                    if ammo > wpn_class.capacity:
                        ammo = wpn_class.capacity
                    self._weapons[count]["ammo"] = ammo

    def recharge_shield(self):
        """
        Replenish shield automatically after specified time interval
        """

        now = pg.time.get_ticks()
        if now - self._last_shield_refresh > REFRESH_SHIELD:
            self._last_shield_refresh = now
            self.shield += 1
            if self.shield > 100:
                self.shield = 100

    def restore(self, level, score, shield, lives, weapons):
        """
        Restore player's status from saved game data
        """

        self.level = level
        self.score = score
        self.shield = shield
        self.lives = lives
        self._weapons = weapons
