from .utils import *
from . import viz_objects
from . import io
from . import atlas 

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
import pyqtgraph as pg
from pyvistaqt import BackgroundPlotter, QtInteractor, MainWindow

class VVASPPlanner(QMainWindow):
    DEFAULT_WIDTH = 2280
    DEFAULT_HEIGHT = 1520
    def __init__(self,
                 experiment_file=None,
                 atlas_name=None,
                 mapping='Beryl',
                 min_tree_depth=None,
                 max_tree_depth=None):
        super(VVASPPlanner,self).__init__()
        self.probe_path_window = None
        self.experiment_file = experiment_file
        self.setWindowTitle('VVASP Surgical Planner')
        self.resize(VVASPPlanner.DEFAULT_WIDTH,VVASPPlanner.DEFAULT_HEIGHT)
        self.objects = []
        self.active_object = None
        self.visible_regions = []
        self.shortcuts_connected = False

        self.vlayout = QVBoxLayout()
        # TODO: Make this work with QDockWidget.
        self.vistaframe = QFrame() # can this be a widget

        # add the pyvista interactor object
        self.plotter = QtInteractor(self.vistaframe, auto_update=True)
        #self.plotter = BackgroundPlotter(True, auto_update=True)
        self.plotter.add_axes()
        self.vlayout.addWidget(self.plotter.interactor)

        self.bottom_horizontal_widgets = QHBoxLayout() #bottom row for interaction
        
        self.vistaframe.setLayout(self.vlayout)
        self.setCentralWidget(self.vistaframe)
        self.vvasp_atlas = atlas.VVASPAtlas(self.plotter, atlas_name=atlas_name, mapping=mapping, min_tree_depth=min_tree_depth, max_tree_depth=max_tree_depth)

        self.plotter.track_click_position(
            callback=lambda x: print(x,flush=True),
            side='left',
            double=True,
            viewport=False)
        # I would add a method to each probe to select which is closer.

        self.initUI() 
        self.vlayout.addLayout(self.bottom_horizontal_widgets)
        self.show()
        if self.experiment_file is not None:
            self._load_experiment(self.experiment_file)
    
    def initUI(self):
        self._init_menubar()
        self._init_probe_position_box()
        self._init_atlas_view_box()
        self._init_keyboard_shortcuts()
        self._init_toolbar()
        self.toggle_probe_path_window()
    
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

        self.probeMenu = self.menubar.addMenu('Objects')
        for object_name, class_to_call in viz_objects.availible_viz_classes_for_gui.items():
            self.probeMenu.addAction(f'Add Object: {object_name}', lambda object_name=object_name, object_class=class_to_call: self.new_object(object_name, object_class))
        self.probeMenu.addAction('Remove Active Object',self.delete_object)
        self.probeMenu.addAction('Next Object',self.next_object)
        self.probeMenu.addAction('Previous Object',self.previous_object)
    
        self.atlasMenu = self.menubar.addMenu('Atlas')
        # TODO: add atlas functionality here

        self.viewMenu = self.menubar.addMenu('Windows')
        # toggleable action
        self.toggle_action = QAction("Probe Path View", self)
        self.toggle_action.setCheckable(True)
        self.toggle_action.triggered.connect(self.toggle_probe_path_window)
        self.viewMenu.addAction(self.toggle_action)
    

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
        self.xangline = QDoubleSpinBox(minimum=-10000,
                                       maximum=10000,
                                       decimals=0,
                                       singleStep=5)
        self.angle_fields.addWidget(self.xangline)
        self.angle_fields.addWidget(QLabel(anglelabels[1]))
        self.yangline = QDoubleSpinBox(minimum=-10000,
                                       maximum=10000,
                                       decimals=0,
                                       singleStep=5)
        self.angle_fields.addWidget(self.yangline)
        self.angle_fields.addWidget(QLabel(anglelabels[2]))
        self.zangline = QDoubleSpinBox(minimum=-10000,
                                       maximum=10000,
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
            #self.objects[self.active_object].set_location(origin,angles)
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
        self.shortcuts_connected = False

    def _update_shortcut_actions(self, disconnect_existing=True): # rebind the actions when a new probe is active
        if disconnect_existing: #handle case where no probe is active yet
            self._disconnect_shortcuts()
        for shortcut, (direction,multiplier) in self.dynamic_shortcuts.items():
            def _shortcut_handler_function(d=direction, m=multiplier):
                self.objects[self.active_object].move(d, m) # connect the function to move the probe
                self.plotter.update()
                self._update_probe_position_text() # update the text box with the new position
                if self.probe_path_window is not None: 
                    self.probe_path_window.update_probe_path_plot() # update the probe path plot
            func = lambda d=direction,m=multiplier:_shortcut_handler_function(d,m)
            shortcut.activated.connect(func)
        self.shortcuts_connected = True

    def _init_atlas_view_box(self):
        if hasattr(self, 'atlas_view_box'):
            return

        self.atlas_view_box = QGroupBox(f'Atlas View: {self.vvasp_atlas.name}')
        self.atlas_view_box.setFixedHeight(300)
        self.atlas_view_box.setFixedWidth(300)

        layout = QVBoxLayout()

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search regions...")
        self.search_bar.textChanged.connect(self.filter_list)  # Connect filtering function

        # List widget
        self.atlas_list_widget = QListWidget()
        self.atlas_list_widget.setSelectionMode(QListWidget.MultiSelection)
        self.atlas_list_widget.setMaximumWidth(200)

        # Store region names
        self.all_region_names = list(self.vvasp_atlas.structures_list_remapped.acronym)

        # Store check states
        self.checked_states = {name: False for name in self.all_region_names}

        # Populate the list initially
        self.populate_list("")

        layout.addWidget(self.search_bar)
        layout.addWidget(self.atlas_list_widget)
        self.atlas_view_box.setLayout(layout)

        self.atlas_list_widget.itemClicked.connect(self.handle_atlas_list_item_click)
        self.bottom_horizontal_widgets.addWidget(self.atlas_view_box)

    def populate_list(self, filter_text=""):
        """Populates the list widget while preserving check states."""
        self.atlas_list_widget.clear()

        for name in self.all_region_names:
            if filter_text.lower() in name.lower():
                item = QListWidgetItem(name)
                item.setCheckState(2 if self.checked_states.get(name, False) else 0)  # Preserve check state
                self.atlas_list_widget.addItem(item)

    def filter_list(self):
        """Filters the list based on user input while keeping check states."""
        # Save the current check states before clearing
        for index in range(self.atlas_list_widget.count()):
            item = self.atlas_list_widget.item(index)
            self.checked_states[item.text()] = item.checkState() == 2  # Checked state is 2

        filter_text = self.search_bar.text().strip()
        self.populate_list(filter_text)

    def _update_atlas_view_box(self):
        for index in range(self.atlas_list_widget.count()):
            item = self.atlas_list_widget.item(index)
            if item.text() in self.vvasp_atlas.visible_atlas_regions:
                item.setCheckState(2)  # 2 represents checked state
            else:
                item.setCheckState(0)  # 0 represents unchecked state 
         
    def handle_atlas_list_item_click(self, item):
        acronym = item.text()
        state = item.checkState()
        if state == 0:
            self.vvasp_atlas.remove_atlas_region_mesh(acronym)
        elif state == 2:
            self.vvasp_atlas.add_atlas_region_mesh(acronym)
        self.plotter.update()

    def _load_experiment(self, experiment_file=None):
        if experiment_file is None:
            self.experiment_file = QFileDialog.getOpenFileName(self, 'Open file', str(io.preferences['default_save_dir']), filter='*.json')[0]
        else:
            self.experiment_file = experiment_file
        # check that experiment file exists
        if not self.experiment_file or not Path(self.experiment_file).exists():
            QMessageBox.critical(self, 'Error', 'Experiment file does not exist or could not be loaded.')
            return
        experiment_data = io.load_experiment_file(self.experiment_file)
        if experiment_data is None:
            return
        print(experiment_data['atlas'], flush=True)

        self.vvasp_atlas = atlas.VVASPAtlas.load_atlas_from_experiment_file(self.experiment_file, self.plotter)

        self.bottom_horizontal_widgets.removeWidget(self.atlas_view_box)
        del self.atlas_view_box
        self._init_atlas_view_box()
        self._update_atlas_view_box()
        if len(self.objects) > 0:
            self._disconnect_shortcuts()
        self.objects = []
        for i,p in enumerate(experiment_data['probes']):
            angles = [p['angles']['elevation'], p['angles']['spin'], p['angles']['azimuth']]
            origin = [p['tip']['ML'], p['tip']['AP'], p['tip']['DV']]
            cls = viz_objects.availible_viz_classes_for_gui[p['probetype']]
            if not 'info' in p.keys():
                p['info'] = f'probe{i}'
            self.objects.append(cls(self.plotter,
                               origin,
                               angles,
                               p['active'],
                               info=p['info'],
                               root_intersection_mesh=self.vvasp_atlas.meshes['root']))
            if p['active']:
                self.active_object = i
        self._update_probe_position_text()
        self._update_shortcut_actions(disconnect_existing=False)
        self.plotter.update()
    
    def _new_experiment(self):
        reply = QMessageBox.question(self, 'Confirm new experiment', "Are you sure you want to create a new experiment? This will clear all probes and the atlas and erase unsaved data.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        if len(self.objects) > 0:
            self._disconnect_shortcuts()
        self.objects = []
        #del self.vvasp_atlas
        self.vvasp_atlas = atlas.VVASPAtlas(self.plotter, mapping='Beryl', min_tree_depth=None, max_tree_depth=None) #TODO: allow the user to update tree depth
        self.active_object = None
        self.experiment_file = None
        self.bottom_horizontal_widgets.removeWidget(self.atlas_view_box)
        del self.atlas_view_box
        self._init_atlas_view_box()
        self._update_atlas_view_box()
        #self._update_probe_position_text()
     
    def _save_experiment(self):
        if self.experiment_file is None:
            self._save_experiment_as()
        else:
            io.save_experiment(self.objects, self.vvasp_atlas, Path(io.preferences['default_save_dir']) / self.experiment_file)
    
    def _screenshot(self):
        experiment_file = QFileDialog.getSaveFileName(self, 'Save screenshot', str(io.preferences['default_save_dir']), filter='*.png')[0]
        if experiment_file: # handle the case where the user cancels the save dialog
            self.experiment_file = experiment_file
            self.plotter.screenshot(self.experiment_file)

    def _save_experiment_as(self):
        experiment_file = Path(QFileDialog.getSaveFileName(self, 'Save file', str(io.preferences['default_save_dir']), filter='*.json')[0])
        if experiment_file: # handle the case where the user cancels the save dialog
            self.experiment_file = experiment_file
            io.save_experiment(self.objects, self.vvasp_atlas, self.experiment_file)
    
    def _export_experiment_as(self):
        experiment_file = Path(QFileDialog.getSaveFileName(self, 'Save file', str(io.EXPERIMENT_DIR), filter='*.txt')[0])
        if experiment_file: # handle the case where the user cancels the save dialog
            self.experiment_file = experiment_file
            io.export_experiment(self.objects, self.vvasp_atlas, self.experiment_file)
     
    def contextMenuEvent(self, e):
        context = QMenu(self)
        for object_name, class_to_call in viz_objects.availible_viz_classes_for_gui.items():
            action = QAction(f'Add object: {object_name}', self)
            func = partial(self.new_object, object_name, class_to_call)
            action.triggered.connect(func)
            context.addAction(action)
        context.exec(e.globalPos())
    
    def new_object(self, object_name, object_class):
        zero_position = [[0,0,0], [90,0,0]]
        info, _ = QInputDialog.getText(self, 'Input Dialog', 'Enter a name for this probe:') 
        new_object = object_class(vistaplotter=self.plotter,
                                  starting_position=[0,0,0],
                                  starting_angles=[90,0,0],
                                  active=True,
                                  root_intersection_mesh=self.vvasp_atlas.meshes['root'],
                                  info=info)
        self.objects.append(new_object)
        active_object = len(self.objects) - 1
        self.update_active_object(active_object)

    def next_object(self):
        if len(self.objects) > 1:
            self.update_active_object((self.active_object + 1) % len(self.objects))
    
    def previous_object(self):
        if len(self.objects) > 1:
            self.update_active_object((self.active_object - 1) % len(self.objects))
    
    def delete_object(self):
        if len(self.objects) > 0:
            self.objects.pop(self.active_object)
            if len(self.objects) > 0:
                self.update_active_object(0)
            else:
                self.active_object = None
                self._update_probe_position_text()
                self._disconnect_shortcuts()
    
    def update_active_object(self, active_object):
        self.active_object = active_object

        # change the object name that gets displayed
        self.probe_position_box.setTitle(f'Probe Position: {self.objects[active_object].info}')
       
        # recolor the objects 
        for (i,prb) in enumerate(self.objects):
            if self.active_object == i:
                prb.make_active() #this recolors the mesh
            else:
                prb.make_inactive()
            self.plotter.update()
        
        # update the positon text
        self._update_probe_position_text()
        # update the probe path plot
        self.probe_path_window.update_probe_path_plot()

        # connect the shortcuts to the new active object
        if self.shortcuts_connected:
            self._update_shortcut_actions(disconnect_existing=True)
        else:
            self._update_shortcut_actions(disconnect_existing=False)
    
    def _update_probe_position_text(self):
        if len(self.objects) == 0: #handle case with no objects present
            self.xline.setValue(0)
            self.yline.setValue(0) 
            self.zline.setValue(0)
            self.depthline.setValue(0)
            self.xangline.setValue(0) 
            self.yangline.setValue(0) 
            self.zangline.setValue(0)
            return
        else:
            prb = self.objects[self.active_object]
        if hasattr(prb, 'root_intersection_mesh'):
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
            self.depthline.setValue(0)

        self.xangline.setValue(prb.angles[0]) 
        self.yangline.setValue(prb.angles[2]) 
        self.zangline.setValue(prb.angles[1])

    def closeEvent(self,event):
        self.plotter.close()
        if self.probe_path_window is not None:
            self.probe_path_window.close()
        event.accept()

    def toggle_probe_path_window(self):
        #if self.toggle_action.isChecked():
        if self.probe_path_window is None: # Create window if it doesn't exist
            #self.text_edit.setStyleSheet("background-color: lightgray;")
            self.probe_path_window = ProbePathWindow(main_window=self)
            self.probe_path_window.show()
        else:
            #self.text_edit.setStyleSheet("background-color: white;")
            self.probe_path_window.close()

#################
## The second window, with probe tracks
#################
class ProbePathWindow(QWidget):
    """Second window that can be opened from the main window."""
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Probe Path View")
        self.setGeometry(300, 300, 400, 800)

        self.update_timer = QTimer(self)
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._update_probe_path_plot)

        layout = QHBoxLayout()
        self.setLayout(layout)
        self.plot = pg.PlotWidget()
        self.plot.setBackground("w")  # Set white background
        self.plot.getPlotItem().hideAxis('bottom')  # Hide X-axis
        self.plot.getPlotItem().getAxis('left').setLabel('Distance from shank tip (um)')
        self.update_probe_path_plot()
        layout.addWidget(self.plot)

    def update_probe_path_plot(self):
        self.update_timer.start(300)  # only update the plot after some time break to not bog down main app
        
    def _update_probe_path_plot(self):
        # get the active probe
        if self.main_window.active_object is None:
            return
        if not hasattr(self.main_window.objects[self.main_window.active_object], 'root_intersection_mesh'):
            self.plot.clear()
            return
        self.plot.clear()
        n_shanks = len(self.main_window.objects[self.main_window.active_object].shank_origins)
        self.plot.setXRange(-1, n_shanks+1)
        boundaries, acronyms = self.main_window.objects[self.main_window.active_object].compute_region_intersections(self.main_window.vvasp_atlas)

        # add the bars to the plot
        for i, (acc, bound) in enumerate(zip(acronyms, boundaries)): # iterate over shanks
            for j, (y0, y1, ac) in enumerate(zip(bound[:-1], bound[1:], acc)): # iterate over regions
                if ac == 'Outside atlas':
                    color = 'gray'
                else:
                    color = self.main_window.vvasp_atlas.meshcolor(ac)
                bar = pg.BarGraphItem(x=i, width=.2, y0=y0 , y1=y1, brush=color)
                self.plot.addItem(bar)
        # add the text of the regions to the plot
        for i, (acc, bound) in enumerate(zip(acronyms, boundaries)): # iterate over shanks
            # get the midpoints of boundaries
            midpts = (bound[:-1] + bound[1:]) / 2
            for j, (ac, mp) in enumerate(zip(acc, midpts)): # iterate over regions
                if ac == 'Outside atlas':
                    color = 'gray'
                else:
                    color = self.main_window.vvasp_atlas.meshcolor(ac)
                text = pg.TextItem(ac, color=color)
                text.setPos(i+.1, mp)  # Position to side of bar
                self.plot.addItem(text)
        
    def closeEvent(self, event):
        self.main_window.probe_path_window = None
        self.main_window.toggle_action.setChecked(False)
        event.accept()
