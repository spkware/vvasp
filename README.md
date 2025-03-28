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
See the `notebooks` folder for examples on rendering atlases and probes. The first time you use a particular atlas, the atlas and meshes will be fetched from brainglobe and saved to your machine. __This will take several minutes while the atlas is fetched from the internet, but will be much faster for subsequent uses.__

### Trajectory Planner Usage
To run the trajectory planning gui, run ``vvasp`` from the terminal. A variety of command line arguments are also exposed to change atlas options and load previous experiments.

#### Changing the scene view
Mouse controls for rotating the 3D scene are as follows (these are determined by [PyVista plottter](https://docs.pyvista.org/api/plotting/plotting)):
| Key                        | Action                                       | Linux/Windows                  | Mac                      |
|----------------------------|----------------------------------------------|--------------------------------|--------------------------|
| `v`                        | Isometric camera view                        | `v`                            | `v`                      |
| `Shift+Click` or `Middle-Click` | Pan the rendering scene                | `Shift+Click` or `Middle-Click` | `Shift+Click`            |
| `Left-Click`               | Rotate the rendering scene in 3D             | `Left-Click`                   | `Cmd+Click`              |
| `Ctrl+Click`               | Rotate the rendering scene in 2D (view-plane) | `Ctrl+Click`                   | `Ctrl+Click`             |
| `Mouse-Wheel` | Continuously zoom the rendering scene | `Mouse-Wheel` or `Right-Click` | `Ctrl+Click`             |
| `Up/Down`                  | Zoom in and out                              | `Up/Down`                      | `Up/Down`                |


#### Add an object to the scene
Probes and other objects can be added through the taskbar (`Objects -> Add Object:`) or by `Right-Click`. All new objects will spawn with their origin placed at bregma.


#### Moving probes or other objects around the scene
Keyboard shortcuts for moving probes around can be found at `~/vvasp/movement_keybinds.json` and `~/vvasp/static_keybinds.json`. These files will be created the first time you run the vvasp gui. If alternate keybinds are desired, just directly edit these files. 

A brief overview of the default keybinds for probe movement:
| Key             | Action                                                     |
|----------------|------------------------------------------------------------|
| `W/A/S/D`      | Move the probe around the AP/ML plane                      |
| `F` / `C`      | Move the probe dorsal and ventral                          |
| `Shift + W/A/S/D` | Adjust the elevation and azimuth angles of the probe  |
| `Shift + F/C`  | Retract or drive the probe along its axis                  |
| `Ctrl + (Key)` | Fine movement modifier (e.g., `Ctrl + D` for smaller right movement) |
| `Ctrl + Shift` | Can be used together for fine and modified movement        |
| `Q/E`         | Control the spin of the probe                               |
| `N/P`         | Switch to the next/previous object in the scene              |
| `H`         | Bring the probe to the home position (bregma)              |
| `Delete`      | Remove the active probe from the scene                      |



__IMPORTANT:__ The buttons used to adjust the probe position by clicking don't work right now. Rather than clicking the buttons with the mouse or manually entering position values, use the keybinds to move the probes where you want.

Currently, the GUI supports Neuropixels 1.0/2.0 alpha/2.0, 10x10 Utah, and [Neuropixels chronic holders](https://github.com/spkware/chronic_holder) (Melin et al. 2024). It also supports loading, viewing, and manipulating any user-provided mesh file (See below).

#### Loading/saving experiments
Experiments can be saved and loaded from the taskbar. All experiment data is written to a `.json` file. This file can be printed out for quick referencing of probe locations during surgery. You can also directly load up a saved experiment in the gui via the command line by specifying `-e` or `--experiment_file` and the path to the experiment file.

#### Custom meshes in the Trajectory Planner
VVASP allows the user to use any of their own meshes for rendering and manipulation. See `CustomMeshObject` for programmatic rendering of custom meshes.

If you want to add your own meshes to the GUI, just drop them in the `custom_user_meshes` folder and then add the `origin` and `angle` transforms to `custom_user_mesh_transformations.json` with the same name as your meshfile. Your custom mesh will be automatically availible next time you load the GUI.

### Integration with PyVista and VTK
Because vvasp uses the default PyVista plotter, all of the PyVista and [VTK](https://github.com/Kitware/VTK) functionality can be leveraged within vvasp. You may want to check out the [PyVista Tutorial](https://tutorial.pyvista.org/tutorial.html)

## Atlases
VVASP currently supports the Allen_25um mouse atlas and the Waxholm_39um rat atlas and will automatically apply the needed transformations to shift the atlases to stereotaxic space (units are in micrometers from bregma). The atlases are fetched from [brainglobe](https://github.com/brainglobe/brainglobe-atlasapi). So any atlas that brainglobe supports should work with VVASP, as long as the necessary transformations are known to shift the atlas from its own coordinate system into stereotaxic space. If there is an atlas you'd like added, please open an issue.