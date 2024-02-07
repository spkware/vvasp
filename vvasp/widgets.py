from .utils import *
from .probe import *

# todo: clean-up QT imports
from PyQt5.QtWidgets import (QWidget,
                             QApplication,
                             QFrame,
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
from PyQt5.QtGui import QImage, QPixmap,QBrush,QPen,QColor,QFont
from PyQt5.QtCore import Qt,QSize,QRectF,QLineF,QPointF,QTimer,QSettings

from pyvistaqt import QtInteractor, MainWindow


class VVASP(QMainWindow):
    def __init__(self,filename=None):
        # filename will be letting you plot the same probes again
        # It'll be just a human readable JSON file.
        super(VVASP,self).__init__()
        self.setWindowTitle('VVASP')
        vlayout = QVBoxLayout()
        # TODO: Make this work with QDockWidget.
        self.vistaframe = QFrame() # can this be a widget

        # add the pyvista interactor object
        self.plotter = QtInteractor(self.vistaframe)

        vlayout.addWidget(self.plotter.interactor)
        
        self.vistaframe.setLayout(vlayout)
        self.setCentralWidget(self.vistaframe)
        if filename is None:
            self.plot_demo()
        self.show()

    def plot_demo(self):
        self.load_atlas()
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
                p.add_mesh(s[0],
                           color = s[1]['rgb_triplet'],
                           opacity = 0.1,silhouette=False)
            else:
                p.add_mesh(s[0],color=s[1]['rgb_triplet'],
                           opacity = 0.7,
                           silhouette=dict(color='#000000',line_width=1) )
        probes = [Probe('24', np.array([-2037,887,-4542]), np.array([80,0,130])),
                  Probe('24', np.array([-1351, 459, -4105]), np.array([70,0,-125])),
                  Probe('24', np.array([-3378, -921, -4672]), np.array([75,75,35])),
                  Probe('24', np.array([-3148, -2477, -3490]), np.array([60,0,-20])),
                  Probe('24', np.array([-1860, -5, -3708]), np.array([45,0,-60]))]
        for prb in probes:
            circ = pv.Sphere(radius=100, center=prb.origin + self.bregma_location)
            p.add_mesh(circ, opacity=1)
            for shnk in prb.shanks:
                rect = pv.Rectangle(shnk.shank_vectors + self.bregma_location)
                #todo: PLOT A BALL AT THE ORIGIN OF THE PROBE
                p.add_mesh(rect,color='#000000',opacity = 1,line_width=3)
         


    def load_atlas(self):
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
