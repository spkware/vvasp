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
                             QMainWindow,
                             QDockWidget,
                             QFileDialog,
                             QDialog,
                             QInputDialog)
from PyQt5.QtGui import QContextMenuEvent, QImage, QPixmap,QBrush,QPen,QColor,QFont
from PyQt5.QtCore import Qt,QSize,QRectF,QLineF,QPointF,QTimer,QSettings

from pyvistaqt import QtInteractor, MainWindow


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
            callback=lambda x: print(x-self.atlas.bregma_location,flush=True),
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
        self.probeMenu.addAction('Remove Active Probe',self.remove_probe)
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
        lineEdits = [QLineEdit() for _ in range(len(xyzlabels))]
        lineEdits2 = [QLineEdit() for _ in range(len(anglelabels))]

        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        for label, line_edit in zip(xyzlabels, lineEdits):
            hbox2 = QHBoxLayout()
            hbox2.addWidget(QLabel(label))
            hbox2.addWidget(line_edit)
            hbox.addLayout(hbox2)
        vbox.addLayout(hbox)

        hbox = QHBoxLayout()
        for label, line_edit in zip(anglelabels, lineEdits2):
            hbox2 = QHBoxLayout()
            hbox2.addWidget(QLabel(label))
            hbox2.addWidget(line_edit)
            hbox.addLayout(hbox2)
        vbox.addLayout(hbox)
        
        self.probe_position_box.setLayout(vbox)

        #TODO: connect the line edits to the probe position
        #for line_edit in self.probe_position_box.lineEdits:
        #    line_edit.textChanged.connect(self.update_probe_position)
        #self.probe_position_box.setFocusPolicy(Qt.StrongFocus)
        #self.probe_position_box.keyPressEvent = self.onKeyPress

        self.probe_position_box.setFixedWidth(700)
        self.bottom_horizontal_widgets.addWidget(self.probe_position_box)
    
    def update_probe_position(self):
        raise NotImplementedError
        self.probes[self.active_probe].move()


    def _init_atlas_view_box(self):
        self.atlas_view_box = QGroupBox(f'Atlas View: {io.preferences["atlas"]}')
        self.atlas_view_box.setLayout(QVBoxLayout())
        self.bottom_horizontal_widgets.addWidget(self.atlas_view_box)


    def _load_experiment(self):
        self.fname = QFileDialog.getOpenFileName(self, 'Open file', str(io.EXPERIMENT_DIR), filter='*.json')[0]
        #TODO: load the file and probes
    
    def _save_experiment(self):
        raise NotImplementedError()
    
    def _save_experiment_as(self):
        savename = QFileDialog.getSaveFileName(self, 'Save file', str(io.EXPERIMENT_DIR), filter='*.json')[0]
        self.fname = savename
        print(savename)
        #TODO: save the file JSON
     
    def contextMenuEvent(self, e):
        context = QMenu(self)
        for p in VAILD_PROBETYPES.keys():
            action = QAction(f'Add object: {p}', self)
            action.triggered.connect(lambda checked, probe_type=p: self.render_new_probe_meshes(probe_type))
            context.addAction(action)
        context.exec(e.globalPos())
    
    def remove_probe(self):
        raise NotImplementedError('The code below was copilot generated and not tested')
        if len(self.probes) > 0:
            self.plotter.remove_actor(self.probes[-1].shanks[0].actor)
            self.probes.pop(-1)
            if self.active_probe == len(self.probes):
                self.active_probe -= 1
            self.update_active_probe_mesh(self.active_probe)


    def render_new_probe_meshes(self, probe_type):
        p = self.plotter
        new_p = Probe(probe_type, np.array([0,0,0]), np.array([0,0,0]))
        self.probes.append(new_p)
        active_probe = len(self.probes) - 1
        for i,prb in enumerate(self.probes):
            for shnk in prb.shanks:
                shnk.actor = p.add_mesh(shnk.mesh,color='#000000',opacity = 1,line_width=3)
        self.update_active_probe_mesh(active_probe)
    
    def update_active_probe_mesh(self, active_probe):
        self.active_probe = active_probe
        p = self.plotter
        print(f'active probe: {self.active_probe}',flush=True)
        for (i,prb) in enumerate(self.probes):
            if self.active_probe == i:
                prb.make_active()
            else:
                prb.make_inactive()
        

    def closeEvent(self,event):
        self.plotter.close()
        event.accept()
