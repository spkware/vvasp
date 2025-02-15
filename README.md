# vvasp
[![DOI](https://zenodo.org/badge/754298641.svg)](https://doi.org/10.5281/zenodo.14873866)

Volume Visualization and Stereotaxic Planning (pronounced wasp 🐝)

<img src="https://github.com/user-attachments/assets/fd96a55b-4a2f-40a4-9c74-dcc47aac1867" width="700">

__This repo is under active development, please post an issue if you encounter any problems, have questions, or would like to suggest a new feature.__
## What is VVASP?

<img src="https://github.com/user-attachments/assets/61e832fe-675f-4448-8465-44de6aa191a0" width="400">

VVASP is a python library for 3D viewing of spatially defined neuroscience data (histology, probe trajectories, neuron locations, etc.). It is built on top of the [PyVista project](https://github.com/pyvista/pyvista) (for mesh visualization) and the [brainglobe atlas API](https://github.com/brainglobe/brainglobe-atlasapi) (for managing brain atlases). It uses the default PyVista plotter and thus fully interops with PyVista functionality.


### VVASP GUI (Trajectory Planner)
In addition to programmatically plotting probes, atlases, and other objects in a notebook, VVASP also includes a graphical user interface to facilitate planning for stereotaxic surgery. The GUI relies on [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) for interactive control and visulization of probe trajectories.


## Installation
To install in develop mode, create a new environment with ``conda create -n [env_name] python=3.10``, activate with ``conda activate [env_name]`` then run ``pip install -e .`` from the repository folder.

## Usage
VVASP can be used in any Jupyter Notebook or Python script, or the VVASP Trajectory Planner GUI can be started from the command line.
### Python scripts and Jupyter notebooks
See the notebooks folder for examples on rendering atlases and probes. The first time you use a particular atlas, the atlas and meshes will be fetched from brainglobe and saved to your machine. __This will take several minutes while the atlas is fetched from the internet, but will be much faster for subsequent uses.__

### Trajectory Planner Usage
To run the trajectory planning gui, run ``vvasp`` from the terminal.

Right click or use the taskbar to add objects to the scene.

Keyboard shortcuts for moving probes around can be found at `~/vvasp/movement_keybinds.json` and `~/vvasp/static_keybinds.json`. These files will be created the first time you run the vvasp gui. If alternate keybinds are desired, just directly edit these files. 

A brief overview of the default keybinds for probe movement:
- WASD moves the probe around the AP/ML plane
- C and F move the probe dorsal and ventral
- Shift is a modifier, so Shift+W/A/S/D adjusts the elevation and azimuth angles of the probe
- Shift+C/F will drive or retract the probe along its axis
- Ctrl is a modifier for fine movement, so Ctrl+D would be smaller movement to the right (Ctrl and Shift can be used together)
- Q and E control the spin of the probe
- N and P switches to the Next and Previous probe in the scene, if there are multiple. The probe highlighted with red is the "active" probe that can be moved around with the keybinds.
- Delete will remove the active probe from the scene


__IMPORTANT:__ The buttons used to adjust the probe position by clicking don't work right now. Rather than clicking the buttons with the mouse or manually entering position values, use the keybinds to move the probes where you want.

Currently, the GUI supports Neuropixels 1.0/2.0 alpha/2.0, 10x10 Utah, and [Neuropixels chronic holders](https://github.com/spkware/chronic_holder) (Melin et al. 2024). It also supports loading, viewing, and manipulating any user-provided mesh file (See below).

Experiments can be saved and loaded from the taskbar.

#### Custom meshes in the Trajectory Planner
VVASP allows the user to use any of their own meshes for rendering and manipulation. See `CustomMeshObject` for programmatic rendering of custom meshes.

If you want to add your own meshes to the GUI, just drop them in the `custom_user_meshes` folder and then add the `origin` and `angle` transforms to `custom_user_mesh_transformations.json` with the same name as your meshfile. Your custom mesh will be automatically availible next time you load the GUI.

### Atlases
VVASP currently supports the Allen_25um mouse atlas and the Waxholm_39um rat atlas and will automatically apply the needed transformations to shift the atlases to stereotaxic space (units are in micrometers from bregma). The atlases are fetched from [brainglobe](https://github.com/brainglobe/brainglobe-atlasapi). So any atlas that brainglobe supports should work with VVASP, as long as the necessary transformations are known to shift the atlas from its own coordinate system into stereotaxic space. If there is an atlas you'd like added, please open an issue.