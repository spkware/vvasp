import numpy as np
import subprocess
import pandas as pd
import pyvista as pv
import sys
import os
from pathlib import Path
import json

from math import cos, sin, radians

def rotation_matrix_from_degrees(x_rot, y_rot, z_rot):
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
    return Rz @ Rx @ Ry # this is the correct order of rotations for the probe

def move3D(distance, phi, theta):
    """Move a point in 3D space by a distance and angles. 
    Max Melin, 2024"""
    theta = radians(theta)
    phi = radians(phi)
    x = -distance * cos(phi) * sin(theta)
    y = distance * cos(phi) * cos(theta)
    z = distance * sin(phi)
    return np.array([x, y, z])

def get_blackrock_array_geometry(nx, ny, pitch_um=400, shank_dims=[40, -1_000, 0]):
    x_positions = np.linspace(0, (nx-1)*pitch_um, nx)
    z_positions = np.linspace(0, (ny-1)*pitch_um, ny) # we are defining defining positions in vvasp space, where the probe shanks are defined on the xz plane (facing forward)
    x_positions = x_positions - np.mean(x_positions) - shank_dims[0]/2#center the probes around the origin (zero)
    z_positions = z_positions - np.mean(z_positions) - shank_dims[2]/2
    y_positions = np.zeros_like(x_positions) #TODO: implement variable z positions for other Blackrock arrays?

    x_grid, y_grid, z_grid = np.meshgrid(x_positions, y_positions, z_positions)
    list_of_coordinates = np.vstack((x_grid.ravel(), y_grid.ravel(), z_grid.ravel())).T.tolist()
    list_of_shank_dims = [shank_dims for _ in range(nx*ny)]
    return list_of_coordinates, list_of_shank_dims

    