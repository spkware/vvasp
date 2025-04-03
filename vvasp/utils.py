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
    """
    Create a 3D rotation matrix from Euler angles in degrees.

    Parameters
    ----------
    x_rot : float
        Rotation angle around x-axis in degrees
    y_rot : float
        Rotation angle around y-axis in degrees
    z_rot : float
        Rotation angle around z-axis in degrees
    order : str, optional
        Order of rotations as string (e.g., 'xyz'). If None, uses default order (z->x->y)

    Returns
    -------
    ndarray
        3x3 rotation matrix

    Notes
    -----
    Default rotation order is y->x->z, which is optimized for probe visualization.
    For custom rotation order, specify as string (e.g., 'xyz' for x->y->z).
    """
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
    """
    Calculate 3D displacement vector from spherical coordinates.

    Parameters
    ----------
    distance : float
        Distance to move in micrometers
    phi : float
        Elevation angle in degrees
    theta : float
        Azimuth angle in degrees

    Returns
    -------
    ndarray
        3D displacement vector [x, y, z] in micrometers
    """
    theta = radians(theta)
    phi = radians(phi)
    x = -distance * cos(phi) * sin(theta)
    y = distance * cos(phi) * cos(theta)
    z = distance * sin(phi)
    return np.array([x, y, z])

def get_blackrock_array_geometry(nx, ny, pitch_um=400, shank_dims=[40, 1_000, 0]):
    """
    Generate geometry for a Blackrock-style multi-shank array.

    Parameters
    ----------
    nx : int
        Number of shanks in x direction
    ny : int
        Number of shanks in y direction
    pitch_um : float, default=400
        Distance between shanks in micrometers
    shank_dims : list, default=[40, 1_000, 0]
        Dimensions of each shank [width, length, thickness] in micrometers

    Returns
    -------
    tuple
        (list_of_coordinates, list_of_shank_dims)
        - list_of_coordinates: List of [x, y, z] positions for each shank
        - list_of_shank_dims: List of shank dimensions for each shank
    """
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
    """
    Implementation of 3D Bresenham's Line Algorithm.

    Generates a sequence of 3D points that approximates a straight line between
    two points using only integer coordinates.

    Parameters
    ----------
    start_point : array-like
        Starting point coordinates [x, y, z] as integers
    end_point : array-like
        Ending point coordinates [x, y, z] as integers

    Returns
    -------
    ndarray
        Array of points along the line with shape (n_points, 3)
    """
    start_point = np.array(start_point, dtype=int)
    end_point = np.array(end_point, dtype=int)
    
    # Calculate deltas and step directions
    deltas = np.abs(end_point - start_point)
    steps = np.sign(end_point - start_point)
    
    # Determine driving axis (axis with maximum delta)
    driving_axis = np.argmax(deltas)
    other_axes = [i for i in range(3) if i != driving_axis]
    
    # Initialize points list with start point
    points = [start_point.copy()]
    current = start_point.copy()
    
    # Initialize error terms
    error_terms = 2 * deltas[other_axes] - deltas[driving_axis]
    
    # Step along driving axis
    while current[driving_axis] != end_point[driving_axis]:
        # Update driving axis
        current[driving_axis] += steps[driving_axis]
        
        # Update other axes if needed
        for i, axis in enumerate(other_axes):
            if error_terms[i] >= 0:
                current[axis] += steps[axis]
                error_terms[i] -= 2 * deltas[driving_axis]
            error_terms[i] += 2 * deltas[axis]
        
        points.append(current.copy())
    
    return np.array(points)

    