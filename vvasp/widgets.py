from fileinput import filename
from matplotlib.artist import get
from .utils import *
from .probe import *
from . import io
from . import atlas_utils 

# todo: clean-up QT imports
from PyQt5.QtWidgets import (QWidget,
                             QApplication,
                             QFrame,
                             QMessageBox,
                             QMenu,
                             QGridLayout,
                             QFormLayout,
                             QVBoxLayout,
                             QHBoxLayout,
                             QTabWidget,
                             QCheckBox,
                             QToolBar,
                             QTextEdit,
                             QLineEdit,
                             QComboBox,
                             QSlider,
                             QPushButton,
                             QLabel,
                             QAction,
                             QListWidget,
                             QWidgetAction,
                             QMenuBar,
                             QDoubleSpinBox,
                             QGraphicsView,
                             QGraphicsScene,
                             QGraphicsItem,
                             QGraphicsLineItem,
                             QListWidgetItem,
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
        self.plotter = QtInteractor(self.vistaframe, auto_update=True)
        self.plotter.add_axes()
        self.vlayout.addWidget(self.plotter.interactor)

        self.bottom_horizontal_widgets = QHBoxLayout() #bottom row for interaction
        
        self.vistaframe.setLayout(self.vlayout)
        self.setCentralWidget(self.vistaframe)

        self.atlas = atlas_utils.Atlas(self.plotter, min_tree_depth=8, max_tree_depth=8) #TODO: allow the user to update tree depth

        self.plotter.track_click_position(
            callback=lambda x: print(x,flush=True),
            side='left',
            double=True,
            viewport=False)
        # I would add a method to each probe to select which is closer.

        self.initUI() 
        self.vlayout.addLayout(self.bottom_horizontal_widgets)
        self.show()
        #if filename is not None: #TODO: implement CLI file load
        #    io.load_experiment(filename)
    
    def initUI(self):
        self._init_menubar()
        self._init_probe_position_box()
        self._init_atlas_view_box()
        self._init_keyboard_shortcuts()
        self._init_toolbar()
    
    def _add_action(self, tool_bar, key, method):
        action = QAction(key, self.app_window)
        action.triggered.connect(method)
        tool_bar.addAction(action)
        return action

    def _init_toolbar(self):
        toolbar = QToolBar(self)
        self.addToolBar(toolbar)
        toolbar.addAction('Camera')
        # TODO: build this out with the camera functionality of the BackgroundPlotter

        
    
    def _init_menubar(self):
        self.menubar = self.menuBar()
        self.fileMenu = self.menubar.addMenu('File')
        self.fileMenu.addAction('New experiment (resets the plotter)', self._new_experiment)
        self.fileMenu.addAction('Load experiment', self._load_experiment)
        self.fileMenu.addAction('Save experiment',self._save_experiment)
        self.fileMenu.addAction('Save experiment as',self._save_experiment_as)
        self.fileMenu.addAction('Screenshot',self._screenshot)
        self.fileMenu.addAction('Quit',self.close)
        self.probeMenu = self.menubar.addMenu('Probe')
        for p in VAILD_PROBETYPES:
            self.probeMenu.addAction(f'Add Probe: {p}', lambda probe_type=p: self.new_probe(probe_type))
        #self.probeMenu.addAction('Remove Active Probe',self.probes[self.active_probe].remove_probe)
        self.probeMenu.addAction('Next Probe',self.next_probe)
        self.probeMenu.addAction('Previous Probe',self.previous_probe)
        self.probeMenu
    
    def _init_probe_position_box(self):
        self.probe_position_box = QGroupBox('Probe Position')
        xyzlabels = ['AP','ML','DV','Depth (along probe axis)']
        anglelabels = ['Elevation', 'Azimuth', 'Roll']

        vbox = QVBoxLayout()

        self.xyz_fields = QHBoxLayout()
        self.xyz_fields.addWidget(QLabel(xyzlabels[0]))
        from PyQt5.QtWidgets import QDoubleSpinBox
        self.xline = QDoubleSpinBox(minimum=-10000,
                                    maximum=10000,
                                    decimals=0,
                                    singleStep=100)
        self.xyz_fields.addWidget(self.xline)
        self.xyz_fields.addWidget(QLabel(xyzlabels[1]))
        self.yline = QDoubleSpinBox(minimum=-10000,
                                    maximum=10000,
                                    decimals=0,
                                    singleStep=100)
        self.xyz_fields.addWidget(self.yline)
        self.xyz_fields.addWidget(QLabel(xyzlabels[2]))
        self.zline = QDoubleSpinBox(minimum=-10000,
                                    maximum=10000,
                                    decimals=0,
                                    singleStep=100)
        self.xyz_fields.addWidget(self.zline)
        self.xyz_fields.addWidget(QLabel(xyzlabels[3]))
        self.depthline = QDoubleSpinBox(minimum=-10000,
                                    maximum=10000,
                                    decimals=0,
                                    singleStep=100)
        self.xyz_fields.addWidget(self.depthline)
        vbox.addLayout(self.xyz_fields)

        self.angle_fields = QHBoxLayout()
        self.angle_fields.addWidget(QLabel(anglelabels[0]))
        self.xangline = QDoubleSpinBox(minimum=-360,
                                       maximum=360,
                                       decimals=0,
                                       singleStep=5)
        self.angle_fields.addWidget(self.xangline)
        self.angle_fields.addWidget(QLabel(anglelabels[1]))
        self.yangline = QDoubleSpinBox(minimum=-360,
                                       maximum=360,
                                       decimals=0,
                                       singleStep=5)
        self.angle_fields.addWidget(self.yangline)
        self.angle_fields.addWidget(QLabel(anglelabels[2]))
        self.zangline = QDoubleSpinBox(minimum=-360,
                                       maximum=360,
                                       decimals=0,
                                       singleStep=5)
        self.angle_fields.addWidget(self.zangline)
        vbox.addLayout(self.angle_fields)
        self.probe_position_box.setLayout(vbox)
        for q in [self.xangline,self.yangline,self.zangline,
                  self.xline,self.yline,self.zline,self.depthline]:
            q.setReadOnly(True) 
        # TODO:link when set to toggle origin position, make not editable otherwise
        def _on_value_changed(value):
            angles = [self.xangline.value(),self.yangline.value(),self.zangline.value()]
            origin = [self.yline.value(),self.xline.value(),self.depthline.value()]
            # try to update if changed
            #self.probes[self.active_probe].set_location(origin,angles)
        #for q in [self.xangline,self.yangline,self.zangline,
        #      self.xline,self.yline]:
        #      q.valueChanged.connect(_on_value_changed)
            
        #TODO: connect the line edits to the probe position
        #for line_edit in self.probe_position_box.lineEdits:
        #    line_edit.textChanged.connect(self.update_probe_position_via_text)
        #self.probe_position_box.setFocusPolicy(Qt.StrongFocus)
        #self.probe_position_box.keyPressEvent = self.onKeyPress

        self.probe_position_box.setFixedWidth(700)
        self.bottom_horizontal_widgets.addWidget(self.probe_position_box)
    
    def _init_keyboard_shortcuts(self):
        # initialize dynamic shortcuts, these change when a new probe is selected
        self.dynamic_shortcuts = {QShortcut(QKeySequence(keypress), self): [action, multiplier] \
            for keypress, (action, multiplier) in io.movement_keybinds.items()}
        # TODO: initialize and connect the static shortcuts
        for keypress,action in io.static_keybinds.items():
            shortcut = QShortcut(QKeySequence(keypress), self)
            if hasattr(self, action) and callable(getattr(self, action)):
                shortcut.activated.connect(eval(f'self.{action}'))
            else:
                print(f'No callable function {action} found for keypress {keypress}',flush=True)
          

    def _disconnect_shortcuts(self):
        for shortcut in self.dynamic_shortcuts.keys():
            shortcut.activated.disconnect()

    def _update_shortcut_actions(self, disconnect_existing=True): # rebind the actions when a new probe is active
        if disconnect_existing: #handle case where no probe is active yet
            self._disconnect_shortcuts()
        for shortcut, (direction,multiplier) in self.dynamic_shortcuts.items():
            def _shortcut_handler_function(d=direction, m=multiplier):
                self.probes[self.active_probe].move(d, m) # connect the function to move the probe
                self._update_probe_position_text() # update the text box with the new position
            func = lambda d=direction,m=multiplier:_shortcut_handler_function(d,m)
            shortcut.activated.connect(func)
            
    def _init_atlas_view_box(self):
        self.atlas_view_box = QGroupBox(f'Atlas View: {io.preferences["atlas"]}')
        self.atlas_view_box.setFixedHeight(300)
        self.atlas_view_box.setFixedWidth(300)

        layout = QHBoxLayout()
        self.atlas_list_widget = QListWidget()
        self.atlas_list_widget.setSelectionMode(QListWidget.MultiSelection)

        for acronym in self.atlas.all_atlas_regions:
            item = QListWidgetItem(acronym)
            item.setCheckState(0)  # 0 represents unchecked state 
            self.atlas_list_widget.addItem(item)
        self.atlas_list_widget.setMaximumWidth(200)
        
        layout.addWidget(self.atlas_list_widget)
        self.atlas_view_box.setLayout(layout)

        self.atlas_list_widget.itemClicked.connect(self.handle_atlas_list_item_click)
        self.bottom_horizontal_widgets.addWidget(self.atlas_view_box)

    def _update_atlas_view_box(self):
        for index in range(self.atlas_list_widget.count()):
            item = self.atlas_list_widget.item(index)
            if item.text() in self.atlas.visible_atlas_regions:
                item.setCheckState(2)  # 2 represents checked state
            else:
                item.setCheckState(0)  # 0 represents unchecked state 
         
    def handle_atlas_list_item_click(self, item):
        acronym = item.text()
        state = item.checkState()
        if state == 0:
            self.atlas.remove_atlas_region_mesh(acronym)
        elif state == 2:
            self.atlas.add_atlas_region_mesh(acronym)

    def _load_experiment(self, filename=None):
        if filename is None:
            self.filename = QFileDialog.getOpenFileName(self, 'Open file', str(io.preferences['default_save_dir']), filter='*.json')[0]
        else:
            self.filename = filename
        experiment_data = io.load_experiment_file(self.filename)
        self.atlas = atlas_utils.Atlas(self.plotter,
                                       atlas_name=experiment_data['atlas']['name'],
                                       min_tree_depth=experiment_data['atlas']['min_tree_depth'],
                                       max_tree_depth=experiment_data['atlas']['max_tree_depth'])

        for r in experiment_data['atlas']['visible_regions']:
            self.atlas.add_atlas_region_mesh(r)
        self._update_atlas_view_box()
        if len(self.probes) > 0:
            self._disconnect_shortcuts()
        self.probes = []
        for i,p in enumerate(experiment_data['probes']):
            angles = [p['angles']['elevation'], p['angles']['spin'], p['angles']['azimuth']]
            origin = [p['tip']['ML'], p['tip']['AP'], p['tip']['DV']]
            self.probes.append(Probe(self.plotter,
                                     p['probetype'],
                                     origin,
                                     angles,
                                     p['active'],
                                     atlas_root_mesh=self.atlas.meshes['root']))
            if p['active']:
                self.active_probe = i
        self._update_probe_position_text()
        self._update_shortcut_actions(disconnect_existing=False)
        self.plotter.update()
    
    def _new_experiment(self):
        reply = QMessageBox.question(self, 'Confirm new experiment', "Are you sure you want to create a new experiment? This will clear all probes and the atlas and erase unsaved data.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        if len(self.probes) > 0:
            self._disconnect_shortcuts()
        self.probes = []
        self.atlas = atlas_utils.Atlas(self.plotter, min_tree_depth=8, max_tree_depth=8) #TODO: allow the user to update tree depth
        self.active_probe = None
        self.filename = None
        self._update_atlas_view_box()
        #self._update_probe_position_text()
     
    def _save_experiment(self):
        if self.filename is None:
            self._save_experiment_as()
        else:
            io.save_experiment(self.probes, self.atlas, Path(io.preferences['default_save_dir']) / self.filename)
    
    def _screenshot(self):
        filename = QFileDialog.getSaveFileName(self, 'Save screenshot', str(io.preferences['default_save_dir']), filter='*.png')[0]
        if filename: # handle the case where the user cancels the save dialog
            self.filename = filename
            self.plotter.screenshot(self.filename)

    def _save_experiment_as(self):
        filename = QFileDialog.getSaveFileName(self, 'Save file', str(io.preferences['default_save_dir']), filter='*.json')[0]
        if filename: # handle the case where the user cancels the save dialog
            self.filename = filename
            io.save_experiment(self.probes, self.atlas, io.EXPERIMENT_DIR / self.filename)
    
    def _export_experiment_as(self):
        filename = QFileDialog.getSaveFileName(self, 'Save file', str(io.EXPERIMENT_DIR), filter='*.txt')[0]
        if filename: # handle the case where the user cancels the save dialog
            self.filename = filename
            io.export_experiment(self.probes, self.atlas, io.EXPERIMENT_DIR / self.filename)
     
    def contextMenuEvent(self, e):
        context = QMenu(self)
        for p in VAILD_PROBETYPES.keys():
            action = QAction(f'Add object: {p}', self)
            action.triggered.connect(lambda checked, probe_type=p: self.new_probe(probe_type))
            context.addAction(action)
        context.exec(e.globalPos())
    
    def new_probe(self, probe_type):
        zero_position = [[0,0,0], [-90,0,0]]
        new_p = Probe(self.plotter, probe_type, *zero_position, atlas_root_mesh=self.atlas.meshes['root']) # the probe object will handle rendering here
        self.probes.append(new_p)
        active_probe = len(self.probes) - 1
        self.update_active_probe(active_probe)
    
    def next_probe(self):
        if len(self.probes) > 0:
            self.update_active_probe((self.active_probe + 1) % len(self.probes))
    
    def previous_probe(self):
        if len(self.probes) > 0:
            self.update_active_probe((self.active_probe - 1) % len(self.probes))
    
    def update_active_probe(self, active_probe):
        self.active_probe = active_probe
        for (i,prb) in enumerate(self.probes):
            if self.active_probe == i:
                prb.make_active() #this recolors the mesh
            else:
                prb.make_inactive()
        self._update_probe_position_text()
        if len(self.probes) > 1:
            self._update_shortcut_actions(disconnect_existing=True)
        else:
            self._update_shortcut_actions(disconnect_existing=False)
    
    def _update_probe_position_text(self):
        prb = self.probes[self.active_probe]
        self.show_entrypoint=True #FIXME: this is a hack to show the entrypoint for the time being
        if self.show_entrypoint:
            if prb.entry_point is not None:
                self.xline.setValue(prb.entry_point[1])
                self.yline.setValue(prb.entry_point[0]) 
                self.zline.setValue(prb.entry_point[2])
                self.depthline.setValue(prb.depth)
            else:
                self.xline.setValue(prb.origin[1]) 
                self.yline.setValue(prb.origin[0])
                self.zline.setValue(prb.origin[2])
                self.depthline.setValue(0)
        else:
            self.xline.setValue(prb.origin[1])
            self.yline.setValue(prb.origin[0]) 
            self.zline.setValue(prb.origin[2])
            self.depthline.setValue(prb.depth)

        self.xangline.setValue(prb.angles[0]) 
        self.yangline.setValue(prb.angles[2]) 
        self.zangline.setValue(prb.angles[1])

    def closeEvent(self,event):
        self.plotter.close()
        event.accept()
