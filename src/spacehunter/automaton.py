"""
automaton.py

This module contains an 'abstract' parent class for an 'instinctive'
computer-controlled game actor.

An Automaton can be assigned one or more of the following 'instincts'
(followed in order of precedence):
    FLEE    - flee (evade) designated target(s) if there are any
    SEEK    - seek (hunt) designated target(s) if there are any
    WANDER  - wander randomly within designated in-play area
    PASSIVE - no autonomous motion - moves solely in response to
              parameters set on initiation or via the set_parameters() command

Target for SEEK or FLEE can be a fixed vector, a sprite or a sprite group.
If the target is a sprite group, the closest sprite in the group will be
targeted by default.

Created on 10 Jun 2020

@author: steely_eyed_missile_man
"""

from math import inf
from random import uniform

import pygame as pg

vec = pg.math.Vector2

"""
Behaviour Modes
"""
SEEK = 1
FLEE = 2
WANDER = 4
PASSIVE = 8

"""
Class constants which govern motion dynamics
Override these to get desired actor behaviour
e.g. faster, stronger, more agile
"""
FACE_DIRECTION_OF_TRAVEL = True
MAX_SPEED = 10
MAX_VELR = 3
MAX_HEALTH = 100
WANDER_INT = 100
WANDER_MAX_TURN = 180
WANDER_RING_RADIUS = 200
WANDER_RING_DISTANCE = 100
APPROACH_RADIUS = 100
SEEK_FORCE = 0.6
FLEE_FORCE = 0.6
FLEE_DISTANCE = 100


class Automaton(pg.sprite.Sprite):
    """
    Automaton sprite class
    """

    def __init__(self, app, img, pos, **kwargs):
        """
        Constructor
        """

        self._app = app  # Pointer to main pygame application instance
        pg.sprite.Sprite.__init__(self)

        self.image = None
        self.image_orig = None
        self.pos = pos
        self.rect = self.set_image(img)
        self.rect.center = self.pos
        self.target = None

        # Process optional keyword arguments
        self.vel = kwargs.get("vel", vec(0, 0))
        self.velr = kwargs.get("velr", 0)
        self.maxvel = kwargs.get("maxvel", MAX_SPEED)
        self.maxvelr = kwargs.get("maxvelr", MAX_VELR)
        self.init_acc = kwargs.get("acc", vec(0, 0))
        self.acc = self.init_acc
        self.accr = kwargs.get("accr", 0)
        self.rot = kwargs.get("rot", 0)
        self.radius = kwargs.get("radius", max(self.rect.width, self.rect.height) / 2)
        self.instinct = kwargs.get("instinct", PASSIVE)
        self.health = kwargs.get("health", MAX_HEALTH)
        self.seek_target = kwargs.get("seek_target", None)
        self._seek_target_pos = None
        self.flee_target = kwargs.get("flee_target", None)
        self._flee_target_pos = None
        self.face_dir_of_travel = kwargs.get("face_dir_of_travel", True)

        self.desired_vec = None
        self.wander_vec = self.vel
        self.last_wander = 0

    def set_image(self, img):
        """
        Override this function to configure image associated with actor
        """

        self.image_orig = img
        self.image = self.image_orig.copy()
        return self.image.get_rect()

    def update(self):
        """
        Update player sprite
        """

        self._apply_instinct()

        # Update velocity vectors
        self.vel += self.acc
        self.velr += self.accr
        if self.vel.length() > self.maxvel:
            self.vel.scale_to_length(self.maxvel)
        if abs(self.velr) > self.maxvelr:
            if self.velr < 0:
                self.velr = -self.maxvelr
            else:
                self.velr = self.maxvelr

        # Update position and orientation
        self.pos += self.vel
        self.rot += self.velr
        if self.face_dir_of_travel:
            self.set_rotation(self.vel_to_dir(self.vel))
        self.rect.center = self.pos

        self._do_events()
        self._check_in_play()
        self._check_health()

    def _apply_instinct(self):
        """
        Override this function to establish custom actor instinct
        """

        if self.instinct & FLEE:
            self.acc = self._flee()
            if self._flee_target_pos is not None:
                return

        if self.instinct & SEEK:
            self.acc = self._seek()
            if self._seek_target_pos is not None:
                return

        if self.instinct & WANDER:
            self.acc = self._wander()
            return

        if self.instinct & PASSIVE:
            self.acc = self.init_acc
            self.accr = 0

    def _do_events(self):
        """
        Override this function to determine how actor responds to
        asynchronous events e.g. user inputs, powerups or collisions
        """

    def _check_health(self):
        """
        Override this function to determine how actor responds to
        diminished or improved health
        """

        if self.health <= 0:
            self.kill()

    def _check_in_play(self):
        """
        Override this function to determine what happens if the actor is 'out of play'
        This may simply govern border reaction, or it may be more sophisticated
        """

        # This is an example implementation which simply wraps the actor
        # to the opposite edge of the display
        if self.pos.x < 0:
            self.pos.x = self._app.width
        if self.pos.x > self._app.width:
            self.pos.x = 0
        if self.pos.y < 0:
            self.pos.y = self._app.height
        if self.pos.y > self._app.height:
            self.pos.y = 0

    def set_rotation(self, angle):
        """
        Rotate actor image
        """

        self.rot = angle % 360
        new_image = pg.transform.rotate(self.image_orig, angle)
        old_center = self.rect.center
        self.image = new_image
        self.rect = self.image.get_rect()
        self.rect.center = old_center

    def _seek(self):
        """
        Seek target(s) specified by set_seek_target()
        """

        self._seek_target_pos = self._get_target_pos(self.seek_target)
        if self._seek_target_pos is None:
            return vec(0, 0)

        self.desired_vec = self._seek_target_pos - self.pos
        dist = self.desired_vec.length()
        self.desired_vec.normalize_ip()
        if dist < APPROACH_RADIUS:
            self.desired_vec *= dist / APPROACH_RADIUS * self.maxvel
        else:
            self.desired_vec *= self.maxvel
        steer = self.desired_vec - self.vel
        if steer.length() > SEEK_FORCE:
            steer.scale_to_length(SEEK_FORCE)
        return steer

    def _flee(self):
        """
        Flee target(s) specified by set_flee_target()
        """

        self._flee_target_pos = self._get_target_pos(self.flee_target)
        if self._flee_target_pos is None:
            return vec(0, 0)

        dist = self.pos - self._flee_target_pos
        if dist.length() < FLEE_DISTANCE:
            self.desired_vec = (
                self.pos - self._flee_target_pos
            ).normalize() * self.maxvel
        else:
            if self.vel.length() == 0:
                self.desired_vec = vec(0, 0)
            else:
                self.desired_vec = self.vel.normalize() * self.maxvel
        steer = self.desired_vec - self.vel
        if steer.length() > FLEE_FORCE:
            steer.scale_to_length(FLEE_FORCE)
        return steer

    def _wander(self):
        """
        Wander around randomly
        """

        now = pg.time.get_ticks()
        if now - self.last_wander > WANDER_INT:
            self.last_wander = now
            self.wander_vec = vec(WANDER_RING_RADIUS, 0).rotate(
                uniform(-WANDER_MAX_TURN, WANDER_MAX_TURN)
            )
        if self.vel.length() == 0:
            future = self.pos + vec(0, 0) * WANDER_RING_DISTANCE
        else:
            future = self.pos + self.vel.normalize() * WANDER_RING_DISTANCE
        self.seek_target = future + self.wander_vec
        return self._seek()

    def _get_target_pos(self, target):
        """
        Get current position of designated target
        """

        if isinstance(target, pg.math.Vector2):
            pos = target
        elif isinstance(target, pg.sprite.Sprite):
            pos = target.pos
        elif isinstance(target, pg.sprite.Group):
            target_spr = self._get_target_sprite(target)
            if target_spr is None:
                pos = None
            else:
                pos = target_spr.pos

        return pos

    def _get_target_sprite(self, sprite_group):
        """
        Find nearest sprite in targeted sprite group
        """

        target_sprite = None

        nearest = inf
        for target in sprite_group:
            tvec = vec(self.pos) - vec(target.pos)
            distance = tvec.magnitude()
            if distance < nearest:
                nearest = distance
                target_sprite = target

        return target_sprite

    def set_parameters(self, **kwargs):
        """
        Set parameters via optional keywords
        """

        self.vel = kwargs.get("vel", self.vel)
        self.velr = kwargs.get("velr", self.velr)
        self.maxvel = kwargs.get("maxvel", self.maxvel)
        self.maxvelr = kwargs.get("maxvelr", self.maxvelr)
        self.acc = kwargs.get("acc", self.acc)
        self.accr = kwargs.get("accr", self.accr)
        self.rot = kwargs.get("rot", self.rot)
        self.radius = kwargs.get("radius", self.radius)
        self.instinct = kwargs.get("instinct", self.instinct)
        self.health = kwargs.get("health", self.health)
        self.seek_target = kwargs.get("seek_target", self.seek_target)
        self.flee_target = kwargs.get("flee_target", self.flee_target)
        self.face_dir_of_travel = kwargs.get(
            "face_dir_of_travel", self.face_dir_of_travel
        )

    def vel_to_dir(self, vel):
        """
        Helper function to convert velocity vector to direction of travel
        relative to display coordinate system
        NB: for clarity, in pygame surface angular coordinates, 0 degrees is
        at the 12 o'clock position, but the Vector2.as_polar() method returns
        an angle where 0 degrees is at the 3 o'clock position (i.e. shifted
        90 degrees)
        """

        _, phi = vel.as_polar()
        if phi > 180:
            angle = phi + 90
        else:
            angle = -phi - 90
        angle = angle if angle > 0 else angle + 360

        return angle
