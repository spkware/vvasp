from tkinter import W
from .utils import *

PREFS_FILE = Path('~').expanduser() / 'vvasp' / 'preferences.json'
MOVEMENT_KEYBINDS_FILE = Path('~').expanduser() / 'vvasp' / 'movement_keybinds.json'
EXPERIMENT_DIR = Path('~').expanduser() / 'vvasp' / 'experiments'
EXPORT_DIR = Path('~').expanduser() / 'vvasp' / 'exports'
ATLAS_DIR = Path('~').expanduser()/'.brainglobe'

DEFAULT_PREFERENCES = {'atlas':'allen_mouse_25um_v1.2',
                        'bregma_locations':{'allen_mouse_25um_v1.2':[216, 18,228],
                                            },
                       'warn_collisions':True,
                       'warn_overwrite':True,
                       'warn_delete':True,}

DEFAULT_MOVEMENT_KEYBINDS = {'a': self.left(1000),
                             'd': ['right', 1000],
                             'f': ['dorsal', 1000],
                             'c': ['ventral', 1000],
                             'w': ['anterior', 1000],
                             's': ['posterior', 1000],
         
                             'Ctrl+a': ['left', 100],
                             'Ctrl+d': ['right', 100],
                             'Ctrl+f': ['dorsal', 100],
                             'Ctrl+c': ['ventral', 100],
                             'Ctrl+w': ['anterior', 100],
                             'Ctrl+s': ['posterior', 100],
         
                             'Shift+a': ['rotate left', 5],
                             'Shift+d': ['rotate right', 5],
                             'Shift+w': ['tilt down', 5],
                             'Shift+s': ['tilt up', 5],
                             'q': ['spin left', 5],
                             'e': ['spin right', 5],
         
                             'Shift+f': ['retract', 1000],
                             'Shift+c': ['advance', 1000],}
         


def __setup_prefs():
    if not EXPERIMENT_DIR.exists():
        print(f'Creating experiment directory at {EXPERIMENT_DIR}')
        EXPERIMENT_DIR.mkdir(parents=True)

    if not EXPORT_DIR.exists():
        print(f'Creating export directory at {EXPORT_DIR}')
        EXPORT_DIR.mkdir()

    if not PREFS_FILE.parent.exists():
        PREFS_FILE.parent.mkdir()

    with open(PREFS_FILE,'w') as fd:
        json.dump(DEFAULT_PREFERENCES,
                  fd,
                  sort_keys=True,
                  indent=4)
    print(f'Preferences file created at {PREFS_FILE}')

    with open(MOVEMENT_KEYBINDS_FILE,'w') as fd:
        json.dump(DEFAULT_MOVEMENT_KEYBINDS,
                  fd,
                  sort_keys=True,
                  indent=4)
    print(f'Keybinds file created at {MOVEMENT_KEYBINDS_FILE}')

def __load_prefs():
    with open(PREFS_FILE,'r') as fd:
        prefs = json.load(fd)
    for k in DEFAULT_PREFERENCES:
        if k not in prefs.keys():
            prefs[k] = DEFAULT_PREFERENCES[k]

    with open(MOVEMENT_KEYBINDS_FILE,'r') as fd:
        keybinds = json.load(fd)
    for k in DEFAULT_MOVEMENT_KEYBINDS:
        if k not in prefs.keys():
            prefs[k] = DEFAULT_MOVEMENT_KEYBINDS[k]

    return prefs, keybinds

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

preferences, movement_keybinds = __load_prefs()