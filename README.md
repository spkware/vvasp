# vvasp
Volume Visualization and Stereotaxic Planning (pronounced wasp 🐝)

__This repo is under active development, please post an issue if you encounter any problems or have questions.__
### What is VVASP?

VVASP is a python library for 3D viewing of spatially defined neuroscience data (histology, probe trajectories, neuron locations, etc.). It is built on top of the [PyVista project](https://github.com/pyvista/pyvista) (for mesh visualization) and the [brainglobe atlas API](https://github.com/brainglobe/brainglobe-atlasapi) (for managing brain atlases). It uses the default PyVista plotter and thus fully interops with PyVista functionality. 

### Installation
To install in develop mode run ``pip install -e .`` from the repository folder.

### Usage
See the notebooks folder for examples on rendering atlases and probes

## VVASP GUI
VVASP also includes a graphical user interface to facilitate planning for stereotaxic surgery. The gui relies on [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) for interactive control and visulization of probe trajectories.

### GUI usage
To run the trajectory planning gui, run ``vvasp`` from the terminal.

Shortcuts for moving probes around can be found at `~/vvasp/movement_keybinds.json` and `~/vvasp/static_keybinds.json`. These files will be created the first time you run the vvasp gui. If alternate keybinds are desired, just directly edit these files. 

Currently, the GUI supports Neuropixels 1.0/2.0, 10x10 Utah, and Neuropixels chronic holders. In the future, it will support loading, viewing, and manipulating any user-provided mesh file.

Experiments can be saved and loaded from the taskbar.