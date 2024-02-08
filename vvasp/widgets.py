from .utils import *
from .probe import *

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
    def __init__(self,filename=None, atlas=None):
        # filename will be letting you plot the same probes again
        # It'll be just a human readable JSON file.
        super(VVASP,self).__init__()
        self.setWindowTitle('VVASP')
        self.resize(VVASP.DEFAULT_WIDTH,VVASP.DEFAULT_HEIGHT)
        self.probes = []
        self.active_probe = None

        vlayout = QVBoxLayout()
        # TODO: Make this work with QDockWidget.
        self.vistaframe = QFrame() # can this be a widget

        # add the pyvista interactor object
        self.plotter = QtInteractor(self.vistaframe)
        self.plotter.add_axes()

        vlayout.addWidget(self.plotter.interactor)
        
        self.vistaframe.setLayout(vlayout)
        self.setCentralWidget(self.vistaframe)
        self.load_atlas(atlas)
        self.show_atlas(atlas)
        self.plotter.track_click_position(
            callback=lambda x: print(x-self.bregma_location,flush=True),
            side='left',
            double=True,
            viewport=False)
        # I would add a method to each probe to select which is closer.

        self.probe_controls = QPushButton('Probe controls here')
        self.show()

    def contextMenuEvent(self, e):
        context = QMenu(self)
        for p in VAILD_PROBETYPES.keys():
            action = QAction(f'Add object: {p}', self)
            action.triggered.connect(lambda checked, probe_type=p: self.render_new_probe_meshes(probe_type))
            context.addAction(action)
        context.exec(e.globalPos())


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
        
    def show_atlas(self, atlas):
        p = self.plotter 
        axes = pv.Axes(show_actor=True, actor_scale=2.0, line_width=5)
        axes.origin = self.bregma_location

        toplot = []
        for acronym in ['root','MOp','CP','VISp','VISa','SCs','ACA','MD']:
            toplot.append(load_structure_mesh(
                self.atlas_location,self.structures,acronym))
        rotate5deg = True

        for s in toplot:
            s[0].rotate_y(90, point=axes.origin, inplace=True) # rotate the meshes so that [x,y,z] => [ML,AP,DV]
            s[0].rotate_x(-90, point=axes.origin, inplace=True)
            if rotate5deg:
                #FIXME: is the following line positive or negative?
                s[0].rotate_x(-5,point=axes.origin, inplace=True) # allenCCF has a 5 degree tilt
            if s[1].acronym == 'root':
                p.add_mesh(s[0].translate(-self.bregma_location), #make bregma the origin
                           color = s[1]['rgb_triplet'],
                           opacity = 0.1,silhouette=False)
            else:
                p.add_mesh(s[0].translate(-self.bregma_location), #make bregma the origin
                           color=s[1]['rgb_triplet'],
                           opacity = 0.7,
                           silhouette=dict(color='#000000',line_width=1))

    def load_atlas(self,atlas):
        self.atlas_location =  Path('~').expanduser()/'.brainglobe'/'allen_mouse_25um_v1.2/'
        with open(self.atlas_location/'structures.json','r') as fd:
            structures = json.load(fd)
        with open(self.atlas_location/'metadata.json','r') as fd:
            self.metadata = json.load(fd)
        self.structures = pd.DataFrame(structures)    
        # AP,DV,ML
        self.bregma_location = np.array([216, 18,228 ])*self.metadata['resolution']

        
    def closeEvent(self,event):
        self.plotter.close()
        event.accept()
