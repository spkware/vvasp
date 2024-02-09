import numpy as np
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


