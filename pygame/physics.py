"""
physics.py - Mathematical physics engine for Chroma-Strand.
Handles vibrating harmonic strings, spring tension slingshot calculations,
ray-triangle/polygon enclosure detection, and kinetic shockwaves.
"""

import math
import pygame
import numpy as np

def distance_sq(p1, p2):
    return (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2

def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def point_line_segment_dist(px, py, x1, y1, x2, y2):
    """Calculates shortest distance from point (px, py) to line segment (x1, y1)-(x2, y2).
    Also returns the projection parameter t clamped between 0 and 1."""
    dx = x2 - x1
    dy = y2 - y1
    l2 = dx * dx + dy * dy
    if l2 == 0:
        return math.hypot(px - x1, py - y1), 0.0, x1, y1
    
    t = ((px - x1) * dx + (py - y1) * dy) / l2
    t = max(0.0, min(1.0, t))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    dist = math.hypot(px - proj_x, py - proj_y)
    return dist, t, proj_x, proj_y

def line_segments_intersect(p1, p2, p3, p4):
    """Returns True and intersection point (x, y) if segment (p1, p2) intersects (p3, p4)."""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4

    denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
    if abs(denom) < 1e-9:
        return False, None

    ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
    ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom

    if 0.0 <= ua <= 1.0 and 0.0 <= ub <= 1.0:
        ix = x1 + ua * (x2 - x1)
        iy = y1 + ua * (y2 - y1)
        return True, (ix, iy)
    return False, None

def is_point_in_polygon(px, py, polygon_points):
    """Ray-casting algorithm for point-in-polygon containment test."""
    n = len(polygon_points)
    inside = False
    p1x, p1y = polygon_points[0]
    for i in range(n + 1):
        p2x, p2y = polygon_points[i % n]
        if py > min(p1y, p2y):
            if py <= max(p1y, p2y):
                if px <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (py - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or px <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def polygon_area(points):
    """Computes area of a 2D polygon using the Shoelace formula."""
    n = len(points)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    return abs(area) * 0.5

def polygon_centroid(points):
    """Computes centroid (center of mass) of polygon points."""
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    return cx, cy

class HarmonicVibration:
    """Simulates realistic acoustic sine-wave vibrations along a light strand."""
    def __init__(self, length):
        self.length = length
        self.amplitude = 0.0
        self.time = 0.0
        self.frequency = max(12.0, min(40.0, 5000.0 / max(50.0, length)))
        self.decay = 5.2 # Exponential damping rate

    def pluck(self, velocity_mag=300.0):
        """Pluck the string with a given impulse."""
        # Amplitude proportional to plucking force, clamped for visual stability
        self.amplitude = min(28.0, 6.0 + (velocity_mag / 40.0))
        self.time = 0.0

    def update(self, dt):
        if self.amplitude > 0.05:
            self.time += dt
            self.amplitude *= math.exp(-self.decay * dt)
        else:
            self.amplitude = 0.0

    def get_displacement_samples(self, num_points=16):
        """Returns normalized sine-wave offsets along string length (0 to 1)."""
        if self.amplitude <= 0.05:
            return None
        phase = self.frequency * self.time * math.tau
        offsets = []
        for i in range(num_points):
            ratio = i / (num_points - 1)
            # Fundamental sine harmonic + 2nd overtone ripple
            disp = (math.sin(math.pi * ratio) * math.sin(phase) +
                    0.25 * math.sin(2 * math.pi * ratio) * math.sin(phase * 2.0))
            offsets.append(disp * self.amplitude)
        return offsets
