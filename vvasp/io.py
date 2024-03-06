from .utils import *
from .default_prefs import (ALL_PREFS, 
                            DEFAULT_PROBE_GEOMETRIES,
                            EXPERIMENT_DIR,
                            EXPORT_DIR,
                            ALL_PREF_FILES, 
                            PREFS_FILE, 
                            DEFAULT_PREFERENCES, 
                            MOVEMENT_KEYBINDS_FILE, 
                            DEFAULT_MOVEMENT_KEYBINDS, 
                            PROBE_GEOMETRIES_FILE,
                            STATIC_KEYBINDS_FILE,
                            DEFAULT_STATIC_KEYBINDS)

def __fix_json_indent(text):
    import re
    return  re.sub('{"', '{\n"', re.sub('\[\[', '[\n[', re.sub('\]\]', ']\n]', re.sub('}', '\n}', text))))

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

    with open(PROBE_GEOMETRIES_FILE,'r') as fd:
        probe_geometries = json.load(fd)
    for k in DEFAULT_PROBE_GEOMETRIES:
        if k not in prefs.keys():
            probe_geometries[k] = DEFAULT_PROBE_GEOMETRIES[k]

    return prefs, movement_keybinds, static_keybinds, probe_geometries

def list_experiments():
    raise NotImplementedError
    return experiments_list

def update_prefs():
    raise NotImplementedError

def save_experiment(probes, atlas, filepath):
    git_commit_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip() # save the version of VVASP this file was created with

    experiment_data = dict(probes = [probe.probe_properties for probe in probes],
                           atlas = atlas.atlas_properties,
                           vvasp_commit_version = git_commit_hash,)
    with open(Path(filepath),'w') as fd:
        json.dump(experiment_data, fd, sort_keys=False, indent=4)


def load_experiment_file(filepath):
    with open(str(filepath),'r') as fd:
        experiment_data = json.load(fd)
    return experiment_data

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

preferences, movement_keybinds, static_keybinds, probe_geometries = __load_prefs()