from .utils import *
from .probe import *
from . import io
from . import atlas_utils 

# todo: clean-up QT imports
from PyQt5.QtWidgets import (QWidget,
                             QApplication,
                             QFrame,
                             QMenu,
                             QGridLayout,
                             QFormLayout,
                             QVBoxLayout,
                             QHBoxLayout,
                             QTabWidget,
                             QCheckBox,
                             QTextEdit,
                             QLineEdit,
                             QComboBox,
                             QSlider,
                             QPushButton,
                             QLabel,
                             QAction,
                             QWidgetAction,
                             QMenuBar,
                             QDoubleSpinBox,
                             QGraphicsView,
                             QGraphicsScene,
                             QGraphicsItem,
                             QGraphicsLineItem,
                             QGroupBox,
                             QTableWidget,
                             QShortcut,
                             QMainWindow,
                             QDockWidget,
                             QFileDialog,
                             QDialog,
                             QInputDialog)
from PyQt5.QtGui import QContextMenuEvent, QImage, QKeyEvent, QPixmap,QBrush,QPen,QColor,QFont,QKeySequence
from PyQt5.QtCore import Qt,QSize,QRectF,QLineF,QPointF,QTimer,QSettings

from pyvistaqt import BackgroundPlotter, QtInteractor, MainWindow


class VVASP(QMainWindow):
    DEFAULT_WIDTH = 2280
    DEFAULT_HEIGHT = 1520
    def __init__(self,filename=None, atlas_name=None):
        # filename will be letting you plot the same probes again
        # It'll be just a human readable JSON file.
        super(VVASP,self).__init__()
        #if filename is not None: #TODO: implement CLI file load 
        #    io.load_experiment(filename)
        self.filename = filename
        self.setWindowTitle('VVASP')
        self.resize(VVASP.DEFAULT_WIDTH,VVASP.DEFAULT_HEIGHT)
        self.probes = []
        self.active_probe = None
        self.visible_regions = []

        self.vlayout = QVBoxLayout()
        # TODO: Make this work with QDockWidget.
        self.vistaframe = QFrame() # can this be a widget

        # add the pyvista interactor object
        self.plotter = QtInteractor(self.vistaframe)
        self.plotter.add_axes()
        self.vlayout.addWidget(self.plotter.interactor)

        self.bottom_horizontal_widgets = QHBoxLayout() #bottom row for interaction
        
        self.vistaframe.setLayout(self.vlayout)
        self.setCentralWidget(self.vistaframe)
        self.atlas = atlas_utils.Atlas(self.plotter, atlas_name) #load the desired atlas
        self.atlas.add_atlas_region_mesh('root')
        self.atlas.add_atlas_region_mesh('CP') #TODO: this is just a placeholder for how we would call this later

        self.plotter.track_click_position(
            callback=lambda x: print(x,flush=True),
            side='left',
            double=True,
            viewport=False)
        # I would add a method to each probe to select which is closer.

        self.initUI() 
        self.vlayout.addLayout(self.bottom_horizontal_widgets)
        self.show()
    
    def initUI(self):
        self._init_menubar()
        self._init_probe_position_box()
        self._init_atlas_view_box()
        self._init_keyboard_shortcuts()
    
    def _init_menubar(self):
        self.menubar = self.menuBar()
        self.fileMenu = self.menubar.addMenu('File')
        self.fileMenu.addAction('Load experiment', self._load_experiment)
        self.fileMenu.addAction('Save experiment',self._save_experiment)
        self.fileMenu.addAction('Save experiment as',self._save_experiment_as)
        self.fileMenu.addAction('Quit',self.close)
        self.probeMenu = self.menubar.addMenu('Probe')
        for p in VAILD_PROBETYPES:
            self.probeMenu.addAction(f'Add Probe: {p}', lambda probe_type=p: self.render_new_probe_meshes(probe_type))
        #self.probeMenu.addAction('Remove Active Probe',self.probes[self.active_probe].remove_probe)
        #self.probeMenu.addAction('Next Probe',self.next_probe)
        #self.probeMenu.addAction('Previous Probe',self.previous_probe)
        #self.probeMenu.addAction('Add Shank',self.add_shank)
        #self.probeMenu.addAction('Remove Shank',self.remove_shank)
        #self.probeMenu.addAction('Next Shank',self.next_shank)
        #self.probeMenu.addAction('Previous Shank',self.previous_shank)
        self.probeMenu
    
    def _init_probe_position_box(self):
        self.probe_position_box = QGroupBox('Probe Position')
        xyzlabels = ['AP','ML','DV','Depth (along probe axis)']
        anglelabels = ['Elevation', 'Azimuth', 'Roll']

        vbox = QVBoxLayout()

        self.xyz_fields = QHBoxLayout()
        self.xyz_fields.addWidget(QLabel(xyzlabels[0]))
        self.xline = QLineEdit()
        self.xyz_fields.addWidget(self.xline)
        self.xyz_fields.addWidget(QLabel(xyzlabels[1]))
        self.yline = QLineEdit()
        self.xyz_fields.addWidget(self.yline)
        self.xyz_fields.addWidget(QLabel(xyzlabels[2]))
        self.zline = QLineEdit()
        self.xyz_fields.addWidget(self.zline)
        vbox.addLayout(self.xyz_fields)

        self.angle_fields = QHBoxLayout()
        self.angle_fields.addWidget(QLabel(anglelabels[0]))
        self.xangline = QLineEdit()
        self.angle_fields.addWidget(self.xangline)
        self.angle_fields.addWidget(QLabel(anglelabels[1]))
        self.yangline = QLineEdit()
        self.angle_fields.addWidget(self.yangline)
        self.angle_fields.addWidget(QLabel(anglelabels[2]))
        self.zangline = QLineEdit()
        self.angle_fields.addWidget(self.zangline)
        vbox.addLayout(self.angle_fields)
        
        self.probe_position_box.setLayout(vbox)

        #TODO: connect the line edits to the probe position
        #for line_edit in self.probe_position_box.lineEdits:
        #    line_edit.textChanged.connect(self.update_probe_position_via_text)
        #self.probe_position_box.setFocusPolicy(Qt.StrongFocus)
        #self.probe_position_box.keyPressEvent = self.onKeyPress

        self.probe_position_box.setFixedWidth(700)
        self.bottom_horizontal_widgets.addWidget(self.probe_position_box)
    
    def _init_keyboard_shortcuts(self):
        self.shortcuts = {
             QShortcut(QKeySequence('a'), self): ['left', 1000], #TODO: move these to preferences.json?
             QShortcut(QKeySequence('Shift+a'), self): ['left', 100], #TODO: move these to preferences.json?
             QShortcut(QKeySequence('d'), self): ['right', 1000],
             QShortcut(QKeySequence('w'), self): ['up', 1000],
             QShortcut(QKeySequence('s'), self): ['down', 1000],
             QShortcut(QKeySequence('w'), self): ['forward', 1000],
             QShortcut(QKeySequence('s'), self): ['backward', 1000],
        }

    def _update_shortcut_actions(self): # rebind the actions when a new probe is active
        for shortcut, (direction,multiplier) in self.shortcuts.items():
            if len(self.probes) > 1: #handle case where no probe is active yet
                shortcut.activated.disconnect()
            print(direction, flush=True)
            print(multiplier, flush=True)

            def _shortcut_handler_function(d=direction, m=multiplier):
                self.probes[self.active_probe].move(d, m) # connect the function to move the probe
                self._update_probe_position_text() # update the text box with the new position
            func = lambda d=direction,m=multiplier:_shortcut_handler_function(d,m)
            shortcut.activated.connect(func)
    

    def _init_atlas_view_box(self):
        self.atlas_view_box = QGroupBox(f'Atlas View: {io.preferences["atlas"]}')
        self.atlas_view_box.setLayout(QVBoxLayout())
        self.bottom_horizontal_widgets.addWidget(self.atlas_view_box)


    def _load_experiment(self):
        self.fname = QFileDialog.getOpenFileName(self, 'Open file', str(io.EXPERIMENT_DIR), filter='*.json')[0]
        #TODO: load the file and probes from io module
    
    def _save_experiment(self):
        raise NotImplementedError()
    
    def _save_experiment_as(self):
        savename = QFileDialog.getSaveFileName(self, 'Save file', str(io.EXPERIMENT_DIR), filter='*.json')[0]
        self.fname = savename
        print(savename)
        #TODO: save the file JSON in io module
     
    def contextMenuEvent(self, e):
        context = QMenu(self)
        for p in VAILD_PROBETYPES.keys():
            action = QAction(f'Add object: {p}', self)
            action.triggered.connect(lambda checked, probe_type=p: self.render_new_probe_meshes(probe_type))
            context.addAction(action)
        context.exec(e.globalPos())
    
    def render_new_probe_meshes(self, probe_type): #TODO: move this over to probe.py like i did for the atlas
        zero_position = [[0,0,0], [0,0,0]]
        new_p = Probe(self.plotter, probe_type, *zero_position) # the probe object will handle rendering here
        self.probes.append(new_p)
        active_probe = len(self.probes) - 1
        self.update_active_probe(active_probe)
    
    def update_active_probe(self, active_probe):
        self.active_probe = active_probe
        print(f'active probe: {self.active_probe}',flush=True)
        for (i,prb) in enumerate(self.probes):
            if self.active_probe == i:
                prb.make_active() #this recolors the mesh
            else:
                prb.make_inactive()
        self._update_probe_position_text()
        self._update_shortcut_actions()
    
    def _update_probe_position_text(self):
        prb = self.probes[self.active_probe]
        self.xline.setText(str(prb.origin[1])) 
        self.yline.setText(str(prb.origin[0])) 
        self.zline.setText(str(prb.origin[2]))
        self.xangline.setText(str(prb.angles[0])) 
        self.yangline.setText(str(prb.angles[1])) 
        self.zangline.setText(str(prb.angles[2]))

    def closeEvent(self,event):
        self.plotter.close()
        event.accept()

