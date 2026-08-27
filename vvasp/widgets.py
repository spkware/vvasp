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
                             QInputDialog,
                             QAbstractSpinBox)

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
        self._updating_probe_position_widgets = False
        self.help_dock_window = None
        self.help_text_widget = None

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
        self._init_probe_path_dock()
        self._init_help_bar()
        self._init_menubar()
        self._init_probe_position_box()
        self._init_probe_list_box()
        self._init_atlas_view_box()
        self._init_keyboard_shortcuts()
        self._init_toolbar()

    def _init_help_bar(self):
        if self.help_dock_window is not None:
            return

        self.help_dock_window = QDockWidget('Help - Keybinds', self)
        self.help_dock_window.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        self.help_dock_window.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)

        container = QWidget(self.help_dock_window)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)

        self.help_text_widget = QTextEdit(container)
        self.help_text_widget.setReadOnly(True)
        self.help_text_widget.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self.help_text_widget)

        self.help_dock_window.setWidget(container)
        self.addDockWidget(Qt.RightDockWidgetArea, self.help_dock_window)
        self.help_dock_window.setVisible(False)

    def _format_help_action(self, action_name):
        if not isinstance(action_name, str):
            return str(action_name)
        return action_name.replace('_', ' ').strip().title()

    def _generate_keybind_help_text(self):
        lines = [
            'VVASP Keybinds',
            '=============',
            '',
            'Built-in:',
            '  F1: Toggle this help bar',
            '',
            'Movement keybinds (active object):',
        ]

        for keypress, (action, multiplier) in sorted(io.movement_keybinds.items(), key=lambda kv: kv[0].lower()):
            lines.append(f'  {keypress}: {self._format_help_action(action)} ({multiplier})')

        lines.append('')
        lines.append('Static keybinds:')
        for keypress, action in sorted(io.static_keybinds.items(), key=lambda kv: kv[0].lower()):
            lines.append(f'  {keypress}: {self._format_help_action(action)}')

        return '\n'.join(lines)

    def _refresh_help_bar_content(self):
        if self.help_text_widget is None:
            return
        self.help_text_widget.setPlainText(self._generate_keybind_help_text())

    def _toggle_help_bar(self):
        if self.help_dock_window is None:
            return
        self._refresh_help_bar_content()
        self.help_dock_window.setVisible(not self.help_dock_window.isVisible())

    def _init_probe_path_dock(self):
        if self.probe_path_window is not None:
            return

        self.probe_path_window = ProbePathDockWidget(main_window=self, parent=self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.probe_path_window)
        self.resizeDocks([self.probe_path_window], [300], Qt.Horizontal)
        self.probe_path_window.setVisible(True)
    
    def _add_action(self, tool_bar, key, method):
        action = QAction(key, self.app_window)
        action.triggered.connect(method)
        tool_bar.addAction(action)
        return action

    def _init_toolbar(self):
        toolbar = QToolBar(self)
        self.camera_toolbar = toolbar
        self.addToolBar(toolbar)
        self.saved_camera_views = {}
        self.camera_view_actions = {}

        toolbar.addAction('Save Custom View', self._save_camera_view)
        toolbar.addAction('Delete Custom View', self._delete_camera_view)
        toolbar.addSeparator()
        toolbar.addAction('X Plane', lambda: self._set_camera_plane('x'))
        toolbar.addAction('Y Plane', lambda: self._set_camera_plane('y'))
        toolbar.addAction('Z Plane', lambda: self._set_camera_plane('z'))
        self.custom_view_separator_action = toolbar.addSeparator()
        toolbar.addAction('Screenshot', self._screenshot)
        toolbar.addSeparator()

    def _set_camera_plane(self, axis):
        """Snap camera to a principal plane view."""
        axis = axis.lower()
        if axis == 'x':
            self.plotter.view_yz()
        elif axis == 'y':
            self.plotter.view_xz()
        elif axis == 'z':
            self.plotter.view_xy()
        else:
            return
        self.plotter.reset_camera()
        self.plotter.update()

    def _save_camera_view(self):
        """Save the current camera position as the next numbered custom view."""
        view_name = self._next_custom_view_name()

        cam_pos = self.plotter.camera_position
        if cam_pos is None:
            QMessageBox.warning(self, 'Camera View', 'No camera position is currently available to save.')
            return

        # Store plain tuples so they are easy to serialize or inspect later.
        self.saved_camera_views[view_name] = tuple(tuple(np.asarray(p, dtype=float)) for p in cam_pos)
        self._add_camera_view_button(view_name)

    def _next_custom_view_name(self):
        """Return the first unused camera view name in the Custom View N sequence."""
        i = 1
        while f'Custom View {i}' in self.saved_camera_views:
            i += 1
        return f'Custom View {i}'

    def _go_to_camera_view(self, view_name):
        """Load a named camera view."""
        if view_name not in self.saved_camera_views:
            return

        self.plotter.camera_position = self.saved_camera_views[view_name]
        self.plotter.reset_camera_clipping_range()
        self.plotter.update()

    def _add_camera_view_button(self, view_name):
        """Ensure a saved camera view has a toolbar button."""
        if view_name in self.camera_view_actions:
            return

        action = QAction(view_name, self)
        action.triggered.connect(lambda checked=False, name=view_name: self._go_to_camera_view(name))
        self.camera_toolbar.insertAction(self.custom_view_separator_action, action)
        self.camera_view_actions[view_name] = action

    def _delete_camera_view(self):
        """Delete a saved camera view and remove its toolbar button."""
        if len(self.saved_camera_views) == 0:
            QMessageBox.information(self, 'Camera View', 'No saved camera views to delete.')
            return

        items = sorted(self.saved_camera_views.keys())
        view_name, ok = QInputDialog.getItem(self, 'Delete Camera View', 'Select view to delete:', items, 0, False)
        if not ok or view_name == '':
            return

        del self.saved_camera_views[view_name]
        action = self.camera_view_actions.pop(view_name, None)
        if action is not None:
            self.camera_toolbar.removeAction(action)

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
        assert self.probe_path_window is not None
        self.toggle_action = self.probe_path_window.toggleViewAction()
        self.toggle_action.setText("Probe Path View")
        self.viewMenu.addAction(self.toggle_action)
        if self.help_dock_window is not None:
            self.help_toggle_action = self.help_dock_window.toggleViewAction()
            self.help_toggle_action.setText('Help Bar')
            self.help_toggle_action.triggered.connect(self._refresh_help_bar_content)
            self.viewMenu.addAction(self.help_toggle_action)

        self.helpMenu = self.menubar.addMenu('Help')
        self.helpMenu.addAction('Show Keybinds', self._toggle_help_bar)
    

    def _init_probe_position_box(self):
        self.probe_position_box = QGroupBox('Probe Position')
        xyzlabels = ['AP','ML','DV','Depth']
        anglelabels = ['Elevation', 'Azimuth', 'Roll']

        vbox = QVBoxLayout()

        def _add_labeled_spinbox(row_layout, label_text, spinbox):
            pair_layout = QHBoxLayout()
            pair_layout.setContentsMargins(0, 0, 0, 0)
            pair_layout.setSpacing(2)
            label = QLabel(label_text)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            pair_layout.addWidget(label)
            spinbox.setMinimumWidth(90)
            spinbox.setMaximumWidth(100)
            pair_layout.addWidget(spinbox)
            pair_layout.setStretch(0, 0)
            pair_layout.setStretch(1, 1)
            row_layout.addLayout(pair_layout, 1)

        self.xyz_fields = QHBoxLayout()
        self.xyz_fields.setSpacing(8)
        self.xline = QDoubleSpinBox(minimum=-10000,
                                    maximum=10000,
                                    decimals=0,
                                    singleStep=100)
        _add_labeled_spinbox(self.xyz_fields, xyzlabels[0], self.xline)
        self.yline = QDoubleSpinBox(minimum=-10000,
                                    maximum=10000,
                                    decimals=0,
                                    singleStep=100)
        _add_labeled_spinbox(self.xyz_fields, xyzlabels[1], self.yline)
        self.zline = QDoubleSpinBox(minimum=-10000,
                                    maximum=10000,
                                    decimals=0,
                                    singleStep=100)
        _add_labeled_spinbox(self.xyz_fields, xyzlabels[2], self.zline)
        self.depthline = QDoubleSpinBox(minimum=-10000,
                                    maximum=10000,
                                    decimals=0,
                                    singleStep=100)
        self.depthline.setToolTip('Depth (along probe axis)')
        _add_labeled_spinbox(self.xyz_fields, xyzlabels[3], self.depthline)
        vbox.addLayout(self.xyz_fields)

        self.angle_fields = QHBoxLayout()
        self.angle_fields.setSpacing(8)
        self.xangline = QDoubleSpinBox(minimum=-10000,
                                       maximum=10000,
                                       decimals=0,
                                       singleStep=5)
        _add_labeled_spinbox(self.angle_fields, anglelabels[0], self.xangline)
        self.yangline = QDoubleSpinBox(minimum=-10000,
                                       maximum=10000,
                                       decimals=0,
                                       singleStep=5)
        _add_labeled_spinbox(self.angle_fields, anglelabels[1], self.yangline)
        self.zangline = QDoubleSpinBox(minimum=-10000,
                                       maximum=10000,
                                       decimals=0,
                                       singleStep=5)
        _add_labeled_spinbox(self.angle_fields, anglelabels[2], self.zangline)
        vbox.addLayout(self.angle_fields)
        self.probe_position_box.setLayout(vbox)

        for q in [self.xangline,self.yangline,self.zangline,
                  self.xline,self.yline,self.zline,self.depthline]:
            q.setKeyboardTracking(False)
            q.valueChanged.connect(self._on_probe_position_spinbox_changed)

        self._update_probe_position_spinbox_editability()

        self.probe_position_box.setFixedWidth(700)
        self.bottom_horizontal_widgets.addWidget(self.probe_position_box)

    def _set_spinbox_editable(self, spinbox, editable):
        spinbox.setReadOnly(not editable)
        spinbox.setButtonSymbols(QAbstractSpinBox.UpDownArrows if editable else QAbstractSpinBox.NoButtons)

    def _update_probe_position_spinbox_editability(self):
        spinboxes = [self.xline, self.yline, self.zline, self.depthline, self.xangline, self.yangline, self.zangline]
        if len(self.objects) == 0 or self.active_object is None:
            for box in spinboxes:
                self._set_spinbox_editable(box, False)
            return

        prb = self.objects[self.active_object]
        for box in [self.xline, self.yline, self.zline, self.xangline, self.yangline, self.zangline]:
            self._set_spinbox_editable(box, True)

        has_entry_drive = hasattr(prb, 'drive_probe_from_entry') and hasattr(prb, 'root_intersection_mesh') and prb.root_intersection_mesh is not None
        self._set_spinbox_editable(self.depthline, has_entry_drive)

        if has_entry_drive:
            # Entry DV is constrained by the mesh intersection and is display-only.
            self._set_spinbox_editable(self.zline, False)

    def _on_probe_position_spinbox_changed(self, _value):
        if self._updating_probe_position_widgets:
            return
        if self.active_object is None or len(self.objects) == 0:
            return

        prb = self.objects[self.active_object]
        angles = np.array([
            self.xangline.value(),
            self.zangline.value(),
            self.yangline.value(),
        ], dtype=float)

        ap = float(self.xline.value())
        ml = float(self.yline.value())
        dv = float(self.zline.value())
        depth = max(0.0, float(self.depthline.value()))
        changed_box = self.sender()

        try:
            has_entry_drive = hasattr(prb, 'drive_probe_from_entry') and hasattr(prb, 'root_intersection_mesh') and prb.root_intersection_mesh is not None
            if has_entry_drive:
                if changed_box in (self.xangline, self.yangline, self.zangline):
                    # Angle edits should rotate around the current tip, not lock to entry point.
                    prb.set_location(np.array(prb.origin, dtype=float), angles)
                elif changed_box in (self.xline, self.yline, self.depthline):
                    prb.drive_probe_from_entry(np.array([ml, ap], dtype=float), angles, depth, root_mesh=prb.root_intersection_mesh)
                else:
                    prb.set_location(np.array(prb.origin, dtype=float), angles)
            else:
                prb.set_location(np.array([ml, ap, dv], dtype=float), angles)
        except Exception as exc:
            print(f'Failed to update probe from spinboxes: {exc}', flush=True)
            return

        self.plotter.update()
        self._update_probe_position_text()
        if self.probe_path_window is not None:
            self.probe_path_window.update_probe_path_plot()
    
    def _init_keyboard_shortcuts(self):
        # initialize dynamic shortcuts, these change when a new probe is selected
        self.dynamic_shortcuts = {QShortcut(QKeySequence(keypress), self): [action, multiplier] \
            for keypress, (action, multiplier) in io.movement_keybinds.items()}
        self.static_shortcuts = {}
        for keypress,action in io.static_keybinds.items():
            shortcut = QShortcut(QKeySequence(keypress), self)
            self.static_shortcuts[keypress] = shortcut
            if hasattr(self, action) and callable(getattr(self, action)):
                shortcut.activated.connect(getattr(self, action))
            else:
                print(f'No callable function {action} found for keypress {keypress}',flush=True)

        self.help_shortcut = QShortcut(QKeySequence('F1'), self)
        self.help_shortcut.activated.connect(self._toggle_help_bar)
          

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

    def _init_probe_list_box(self):
        if hasattr(self, 'probe_list_box'):
            return

        self.probe_list_box = QGroupBox('Probes (0)')
        self.probe_list_box.setFixedHeight(300)
        self.probe_list_box.setFixedWidth(260)

        layout = QVBoxLayout()
        self.probe_list_widget = QListWidget()
        self.probe_list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.probe_list_widget.itemClicked.connect(self._handle_probe_list_item_click)

        layout.addWidget(self.probe_list_widget)
        self.probe_list_box.setLayout(layout)
        self.bottom_horizontal_widgets.addWidget(self.probe_list_box)

    def _refresh_probe_list_box(self):
        if not hasattr(self, 'probe_list_widget'):
            return

        self.probe_list_widget.blockSignals(True)
        self.probe_list_widget.clear()
        for idx, obj in enumerate(self.objects):
            display_name = getattr(obj, 'info', None) or getattr(obj, 'name', f'Probe {idx + 1}')
            item = QListWidgetItem(f'{idx + 1}: {display_name}')
            item.setData(Qt.UserRole, idx)
            if self.active_object == idx:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                item.setBackground(QColor(220, 240, 255))
                self.probe_list_widget.addItem(item)
                self.probe_list_widget.setCurrentItem(item)
            else:
                self.probe_list_widget.addItem(item)
        self.probe_list_widget.blockSignals(False)
        self.probe_list_box.setTitle(f'Probes ({len(self.objects)})')

    def _handle_probe_list_item_click(self, item):
        idx = item.data(Qt.UserRole)
        if idx is None:
            return
        if idx != self.active_object:
            self.update_active_object(idx)

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
        if len(self.objects) > 0 and self.active_object is None:
            self.active_object = 0
        self._refresh_probe_list_box()
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
        self._refresh_probe_list_box()
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
                self._refresh_probe_list_box()
    
    def update_active_object(self, active_object):
        self.active_object = active_object
        self._refresh_probe_list_box()
        self._update_probe_position_spinbox_editability()

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
        if self.probe_path_window is not None:
            self.probe_path_window.update_probe_path_plot()

        # connect the shortcuts to the new active object
        if self.shortcuts_connected:
            self._update_shortcut_actions(disconnect_existing=True)
        else:
            self._update_shortcut_actions(disconnect_existing=False)
    
    def _update_probe_position_text(self):
        self._updating_probe_position_widgets = True
        try:
            if len(self.objects) == 0 or self.active_object is None: #handle case with no objects present
                self.xline.setValue(0)
                self.yline.setValue(0)
                self.zline.setValue(0)
                self.depthline.setValue(0)
                self.xangline.setValue(0)
                self.yangline.setValue(0)
                self.zangline.setValue(0)
                return

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
        finally:
            self._updating_probe_position_widgets = False
        self._update_probe_position_spinbox_editability()

    def closeEvent(self,event):
        self.plotter.close()
        if self.probe_path_window is not None:
            self.probe_path_window.close()
        event.accept()

#################
## The dock widget, with probe tracks
#################
class ProbePathDockWidget(QDockWidget):
    """Dock widget that shows probe tracks inside the main window."""
    def __init__(self, main_window, parent=None):
        super().__init__("Probe Path View", parent)
        self.main_window = main_window
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)
        self.setMinimumWidth(20)
        self.setMaximumWidth(520)
        self.setContentsMargins(6, 6, 6, 6)
        self.setStyleSheet("QDockWidget { border: 1px solid palette(mid); }")

        title_bar = QWidget(self)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(8, 4, 8, 4)
        title_layout.setSpacing(0)
        title_label = QLabel("Probe Path View")
        title_layout.addWidget(title_label)
        title_layout.addStretch(1)
        self.setTitleBarWidget(title_bar)

        self.update_timer = QTimer(self)
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._update_probe_path_plot)

        container = QWidget(self)
        container.setMinimumWidth(0)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        self.plot = pg.PlotWidget()
        self.plot.setMinimumWidth(0)
        self.plot.setBackground("w")  # Set white background
        self.plot.getPlotItem().hideAxis('bottom')  # Hide X-axis
        self.plot.getPlotItem().getAxis('left').setLabel('Distance from shank tip (um)')
        self.update_probe_path_plot()
        layout.addWidget(self.plot)
        self.setWidget(container)

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
        boundaries, acronyms = self.main_window.objects[self.main_window.active_object].compute_region_intersections(self.main_window.vvasp_atlas)
        max_depth = max((bound[-1] for bound in boundaries), default=0)
        self.plot.setRange(xRange=(-0.5, max(n_shanks - 0.5, 0.5)), yRange=(0, max_depth), padding=0.05)

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
        
