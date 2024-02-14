from tkinter import W
from .utils import *

PREFS_FILE = Path('~').expanduser() / 'vvasp' / 'preferences.json'
MOVEMENT_KEYBINDS_FILE = Path('~').expanduser() / 'vvasp' / 'movement_keybinds.json'
STATIC_KEYBINDS_FILE = Path('~').expanduser() / 'vvasp' / 'static_keybinds.json'
EXPERIMENT_DIR = Path('~').expanduser() / 'vvasp' / 'experiments'
EXPORT_DIR = Path('~').expanduser() / 'vvasp' / 'exports'
ATLAS_DIR = Path('~').expanduser()/'.brainglobe'

ALL_PREF_FILES = [PREFS_FILE, MOVEMENT_KEYBINDS_FILE, STATIC_KEYBINDS_FILE]

DEFAULT_PREFERENCES = {'atlas':'allen_mouse_25um_v1.2',
                        'bregma_locations':{'allen_mouse_25um_v1.2':[216, 18,228],
                                            },
                       'warn_collisions':True,
                       'warn_overwrite':True,
                       'warn_delete':True,}

DEFAULT_MOVEMENT_KEYBINDS = {'a': ['left', 100],
                             'd': ['right', 100],
                             'f': ['dorsal', 100],
                             'c': ['ventral', 100],
                             'w': ['anterior', 100],
                             's': ['posterior', 100],
         
                             'Ctrl+a': ['left', 10],
                             'Ctrl+d': ['right', 10],
                             'Ctrl+f': ['dorsal', 10],
                             'Ctrl+c': ['ventral', 10],
                             'Ctrl+w': ['anterior', 10],
                             'Ctrl+s': ['posterior', 10],
         
                             'Shift+a': ['rotate left', 5],
                             'Shift+d': ['rotate right', 5],
                             'Shift+w': ['tilt down', 5],
                             'Shift+s': ['tilt up', 5],

                             'Ctrl+Shift+a': ['rotate left', 1],
                             'Ctrl+Shift+d': ['rotate right', 1],
                             'Ctrl+Shift+w': ['tilt down', 1],
                             'Ctrl+Shift+s': ['tilt up', 1],
                             
                             'q': ['spin left', 5],
                             'e': ['spin right', 5],

                             'Ctrl+q': ['spin left', 1],
                             'Ctrl+e': ['spin right', 1],
         
                             'Shift+f': ['retract', 100],
                             'Shift+c': ['advance', 100],
                             'Ctrl+Shift+f': ['retract', 10],
                             'Ctrl+Shift+c': ['advance', 10],}

DEFAULT_STATIC_KEYBINDS = {'Ctrl+o': 'open_experiment',
                           #'Ctrl+s': 'save',
                           #'Ctrl+Shift+s': 'save as',
                           #'Ctrl+Shift+o': 'open',
                           #'Ctrl+e': 'export',
                           #'Ctrl+Shift+e': 'export as',
                           'n': 'next_probe',
                           'p': 'previous_probe',}

ALL_PREFS = [DEFAULT_PREFERENCES, DEFAULT_MOVEMENT_KEYBINDS, DEFAULT_STATIC_KEYBINDS]
                           
         


def __setup_prefs():
    if not EXPERIMENT_DIR.exists():
        print(f'Creating experiment directory at {EXPERIMENT_DIR}')
        EXPERIMENT_DIR.mkdir(parents=True)

    if not EXPORT_DIR.exists():
        print(f'Creating export directory at {EXPORT_DIR}')
        EXPORT_DIR.mkdir()

    if not PREFS_FILE.parent.exists():
        PREFS_FILE.parent.mkdir()

    for fpath, prefs in zip(ALL_PREF_FILES, ALL_PREFS):
        with open(fpath,'w') as fd:
            json.dump(prefs,
                      fd,
                      sort_keys=True,
                      indent=4)
        print(f'Preferences file created at {fpath}')

def __load_prefs():
    with open(PREFS_FILE,'r') as fd:
        prefs = json.load(fd)
    for k in DEFAULT_PREFERENCES:
        if k not in prefs.keys():
            prefs[k] = DEFAULT_PREFERENCES[k]

    with open(MOVEMENT_KEYBINDS_FILE,'r') as fd:
        movement_keybinds = json.load(fd)
    for k in DEFAULT_MOVEMENT_KEYBINDS:
        if k not in prefs.keys():
            movement_keybinds[k] = DEFAULT_MOVEMENT_KEYBINDS[k]

    with open(STATIC_KEYBINDS_FILE,'r') as fd:
        static_keybinds = json.load(fd)
    for k in DEFAULT_STATIC_KEYBINDS:
        if k not in prefs.keys():
            static_keybinds[k] = DEFAULT_STATIC_KEYBINDS[k]

    return prefs, movement_keybinds, static_keybinds

def list_experiments():
    raise NotImplementedError
    return experiments_list

def update_prefs():
    raise NotImplementedError

def save_experiment():
    raise NotImplementedError

def save_experiment_as():
    raise NotImplementedError

def load_experiment():
    raise NotImplementedError

def load_structure_mesh(atlaspath,structures,acronym):
    # meshes are in um
    id = structures[structures.acronym == acronym].id.values
    if len(id):
        id = id[0]
    else:
        return
    mesh = atlaspath/'meshes'/f'{id}.obj'
    mesh = pv.read(mesh)
    return mesh, structures[structures.acronym == acronym].iloc[0]


if not PREFS_FILE.exists():
    __setup_prefs()

preferences, movement_keybinds, static_keybinds = __load_prefs()