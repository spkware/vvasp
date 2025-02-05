# vvasp
Volume Visualization and Stereotaxic Planning (pronounced wasp 🐝)

__This repo is under active development, please post an issue if you encounter any problems or have questions.__
## What is VVASP?

VVASP is a python library for 3D viewing of spatially defined neuroscience data (histology, probe trajectories, neuron locations, etc.). It is built on top of the [PyVista project](https://github.com/pyvista/pyvista) (for mesh visualization) and the [brainglobe atlas API](https://github.com/brainglobe/brainglobe-atlasapi) (for managing brain atlases). It uses the default PyVista plotter and thus fully interops with PyVista functionality. 

## VVASP GUI (Trajectory Planner)
VVASP also includes a graphical user interface to facilitate planning for stereotaxic surgery. The gui relies on [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) for interactive control and visulization of probe trajectories.

### Installation
To install in develop mode run ``pip install -e .`` from the repository folder.

### Usage
See the notebooks folder for examples on rendering atlases and probes. The first time you use a particular atlas, the atlas and meshes will be fetched from brainglobe and saved to your machine.

### Trajectory Planner Usage
To run the trajectory planning gui, run ``vvasp`` from the terminal.

Keyboard shortcuts for moving probes around can be found at `~/vvasp/movement_keybinds.json` and `~/vvasp/static_keybinds.json`. These files will be created the first time you run the vvasp gui. If alternate keybinds are desired, just directly edit these files. 

__IMPORTANT:__ The buttons contained in the GUI don't work right now. Rather than clicking the buttons with the mouse or manually entering position values, use the keybinds to move the probes where you want.

Currently, the GUI supports Neuropixels 1.0/2.0 alpha/2.0, 10x10 Utah, and [Neuropixels chronic holders](https://github.com/spkware/chronic_holder) (Melin et al. 2024). In the future, it will support loading, viewing, and manipulating any user-provided mesh file.

Experiments can be saved and loaded from the taskbar.

### Atlases
VVASP currently supports the Allen_25um mouse atlas and the Waxholm_39um rat atlas and will automatically apply the needed transformations to shift the atlases to stereotaxic space (units are in micrometers from bregma). The atlases are fetched from [brainglobe](https://github.com/brainglobe/brainglobe-atlasapi). So any atlas that brainglobe supports should work with VVASP, as long as the necessary transformations are known to shift the atlas from its own coordinate system into stereotaxic space. If there is an atlas you'd like added, please open an issue.