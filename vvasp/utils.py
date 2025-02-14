import numpy as np
import subprocess
from functools import partial
import pandas as pd
import pyvista as pv
import sys
import os
from pathlib import Path
import json

from math import cos, sin, radians

def rotation_matrix_from_degrees(x_rot, y_rot, z_rot, order=None):
    """Return a rotation matrix to rotate a vector in 3D space. Pass the angles in degrees, not radians.
    Max Melin, 2024"""
    alpha = radians(z_rot)
    beta = radians(y_rot)
    gamma = radians(x_rot)

    Rz = np.array([[cos(alpha), -sin(alpha), 0],
                     [sin(alpha), cos(alpha), 0],
                     [0, 0, 1]])
    Ry = np.array([[cos(beta), 0, sin(beta)],
                   [0, 1, 0],
                   [-sin(beta), 0, cos(beta)]])
    Rx = np.array([[1,0,0],
                   [0, cos(gamma), -sin(gamma)],
                   [0, sin(gamma), cos(gamma)]])

    #return Rz @ Ry @ Rx
    if order is None:
        return Rz @ Rx @ Ry # this is the correct order of rotations for the probe
    else:
        rdict = dict(x=Rx, y=Ry, z=Rz)
        return rdict[order[2]] @ rdict[order[1]] @ rdict[order[0]]

def move3D(distance, phi, theta):
    """Move a point in 3D space by a distance and angles. 
    Max Melin, 2024"""
    theta = radians(theta)
    phi = radians(phi)
    x = -distance * cos(phi) * sin(theta)
    y = distance * cos(phi) * cos(theta)
    z = distance * sin(phi)
    return np.array([x, y, z])

def get_blackrock_array_geometry(nx, ny, pitch_um=400, shank_dims=[40, 1_000, 0]):
    x_positions = np.linspace(0, (nx-1)*pitch_um, nx)
    z_positions = np.linspace(0, (ny-1)*pitch_um, ny) # we are defining defining positions in vvasp space, where the probe shanks are defined on the xz plane (facing forward)
    x_positions = x_positions - np.mean(x_positions) - shank_dims[0]/2#center the probes around the origin (zero)
    z_positions = z_positions - np.mean(z_positions) - shank_dims[2]/2
    y_positions = np.zeros_like(x_positions) - shank_dims[1] #TODO: implement variable z positions for other Blackrock arrays?

    x_grid, y_grid, z_grid = np.meshgrid(x_positions, y_positions, z_positions)
    list_of_coordinates = np.vstack((x_grid.ravel(), y_grid.ravel(), z_grid.ravel())).T.tolist()
    list_of_coordinates = list_of_coordinates[:(nx*ny)]
    list_of_shank_dims = [shank_dims for _ in range(nx*ny)]
    return list_of_coordinates, list_of_shank_dims

def bresenham3D(start_point, end_point):
    '''
    Implementation of 3D Bresenham Line Algorithm. Start point and end point should be a tuple or array of 3 integers.
    '''
    start_point = np.array(start_point, dtype=int)
    end_point = np.array(end_point, dtype=int)
    
    x1, y1, z1 = start_point
    x2, y2, z2 = end_point
    points = []
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    dz = abs(z2 - z1)
    
    xs = 1 if x2 > x1 else -1
    ys = 1 if y2 > y1 else -1
    zs = 1 if z2 > z1 else -1
    
    # Driving axis is X-axis
    if dx >= dy and dx >= dz:
        p1 = 2 * dy - dx
        p2 = 2 * dz - dx
        while x1 != x2:
            points.append((x1, y1, z1))
            if p1 >= 0:
                y1 += ys
                p1 -= 2 * dx
            if p2 >= 0:
                z1 += zs
                p2 -= 2 * dx
            p1 += 2 * dy
            p2 += 2 * dz
            x1 += xs
    
    # Driving axis is Y-axis
    elif dy >= dx and dy >= dz:
        p1 = 2 * dx - dy
        p2 = 2 * dz - dy
        while y1 != y2:
            points.append((x1, y1, z1))
            if p1 >= 0:
                x1 += xs
                p1 -= 2 * dy
            if p2 >= 0:
                z1 += zs
                p2 -= 2 * dy
            p1 += 2 * dx
            p2 += 2 * dz
            y1 += ys
    
    # Driving axis is Z-axis
    else:
        p1 = 2 * dx - dz
        p2 = 2 * dy - dz
        while z1 != z2:
            points.append((x1, y1, z1))
            if p1 >= 0:
                x1 += xs
                p1 -= 2 * dz
            if p2 >= 0:
                y1 += ys
                p2 -= 2 * dz
            p1 += 2 * dx
            p2 += 2 * dy
            z1 += zs
    
    points.append((x2, y2, z2))  # Ensure the last point is included
    return np.stack(points)

    