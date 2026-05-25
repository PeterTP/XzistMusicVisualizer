from PySide6.QtWidgets import QDockWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QRadioButton, QScrollArea, QFrame, QComboBox, QCheckBox
from PySide6.QtCore import Qt, QMargins
import pyqtgraph as pg  # import order MATTERS (putting pyqtgraph before pyside will fail)
import pyqtgraph.exporters
import numpy as np
import librosa
import colorsys


class Graph2D:
    def __init__(self, win, PATH, update_chunk_size):
        self.win = win
        self.PATH = PATH
        self.update_chunk_size = update_chunk_size

        self.sr = 48000
        self.chunk_size = 4096
        self.default_graph_size = {
            'y1':-7, 'y2':20,
            'x1':1, 'x2':4.35
        }
        self.lerp_amount = .75
        self.sigmoid_amount = .5
        self.use_custom_log = True
        self.log_base = (10,2)
        self.color_hue = .75
        self.color_range = 1
        self.sigmoid_limit = 20
        self.sigmoid_gradient = .1
        self.average_amp = 1
        self.plot_data = {'wave':{}, 'stft':{}, 'mel':{}}

        pg.setConfigOptions(useOpenGL=True, antialias=True)
        self.set_plot_data()
        self.create_docks()
        

    def create_docks(self):
        def reset_graph_scaling():
            s = self.default_graph_size
            self.graph.disableAutoRange()
            self.graph.setYRange(s['y1'], s['y2'], padding=0)
            self.graph.setXRange(s['x1'], s['x2'], padding=0)


        def set_preset():
            
            match(presets_combobox.currentText()):
                case '1024':
                    self.default_graph_size = {
                        'y1': -7, 'y2': 20,
                        'x1': 1.5, 'x2': 4.35
                    }
                    hide_axis_checkbox.setChecked(False)
                    x_log_checkbox.setChecked(True)
                    y_height_slider.setValue(20)
                    color_hue_slider.setValue(.75*100)
                    color_range_slider.setValue(1*10)
                    lerp_slider.setValue(.85*100)
                    log_sigmoid_slider.setValue(.5*100)
                    sigmoid_limit_slider.setValue(30)
                    sigmoid_gradient_slider.setValue(1*100)
                    chunk_combobox.setCurrentText('1024')
                    mel_radio.setChecked(True)

                case '2048':
                    self.default_graph_size = {
                        'y1': -7, 'y2': 20,
                        'x1': 1.2, 'x2': 4.35
                    }
                    hide_axis_checkbox.setChecked(False)
                    x_log_checkbox.setChecked(True)
                    y_height_slider.setValue(20)
                    color_hue_slider.setValue(.75*100)
                    color_range_slider.setValue(2*10)
                    lerp_slider.setValue(.8*100)
                    log_sigmoid_slider.setValue(.5*100)
                    sigmoid_limit_slider.setValue(20)
                    sigmoid_gradient_slider.setValue(.2*100)
                    chunk_combobox.setCurrentText('2048')
                    mel_radio.setChecked(True)

                case '4096':
                    self.default_graph_size = {
                        'y1': -7, 'y2': 20,
                        'x1': 1, 'x2': 4.35
                    }
                    hide_axis_checkbox.setChecked(False)
                    x_log_checkbox.setChecked(True)
                    y_height_slider.setValue(20)
                    color_hue_slider.setValue(.75*100)
                    color_range_slider.setValue(1*10)
                    lerp_slider.setValue(.75*100)
                    log_sigmoid_slider.setValue(.5*100)
                    sigmoid_limit_slider.setValue(20)
                    sigmoid_gradient_slider.setValue(.1*100)
                    chunk_combobox.setCurrentText('4096')
                    mel_radio.setChecked(True)

                case '8192':
                    self.default_graph_size = {
                        'y1': -7, 'y2': 20,
                        'x1': .6, 'x2': 4.35
                    }
                    hide_axis_checkbox.setChecked(False)
                    x_log_checkbox.setChecked(True)
                    y_height_slider.setValue(25)
                    color_hue_slider.setValue(.75*100)
                    color_range_slider.setValue(1*10)
                    lerp_slider.setValue(.5*100)
                    log_sigmoid_slider.setValue(.7*100)
                    sigmoid_limit_slider.setValue(25)
                    sigmoid_gradient_slider.setValue(.01*100)
                    chunk_combobox.setCurrentText('8192')
                    mel_radio.setChecked(True)

            set_transform()
            set_chunk_size()
            set_hide_axis()
            set_log()
            set_height()
            set_color()
            set_lerp()
            set_log_sigmoid()
            set_sigmoid_options()


        def set_hide_axis():
            if hide_axis_checkbox.isChecked():
                self.graph.plotItem.hideAxis('left')
                self.graph.plotItem.hideAxis('bottom')
            else:
                self.graph.plotItem.showAxis('left')
                self.graph.plotItem.showAxis('bottom')


        def set_log():
            self.use_custom_log = x_log_checkbox.isChecked()
            self.graph.setLogMode(self.use_custom_log, False)

            if self.use_custom_log and not self.plot_data['wave']['is_on']:
                reset_graph_scaling()

            self.graph.disableAutoRange()


        def set_height():
            self.graph.setYRange(-7, y_height_slider.value(), padding=0)
            y_height_label.setText(f'Y Height: {y_height_slider.value():.2f}')


        def set_color():
            self.color_hue = color_hue_slider.value()/100
            self.color_range = color_range_slider.value()/10
            color_label.setText(f'Color Hue: {self.color_hue:.2f} | Range: {self.color_range:.2f}')


        def set_lerp():
            self.lerp_amount = lerp_slider.value()/100
            lerp_label.setText(f'Lerp Smoothing: {self.lerp_amount:.2f}')


        def set_log_sigmoid():
            self.sigmoid_amount = log_sigmoid_slider.value()/100
            log_sigmoid_label.setText(f'Log/Sigmoid Ratio: {self.sigmoid_amount:.2f}')


        def set_sigmoid_options():
            self.sigmoid_limit = sigmoid_limit_slider.value()
            self.sigmoid_gradient = sigmoid_gradient_slider.value()/100
            sigmoid_options_label.setText(f'Sigmoid Limit: {self.sigmoid_limit:.2f} | Gradient: {self.sigmoid_gradient:.2f}')


        def set_chunk_size():
            size = int(chunk_combobox.currentText())
            self.chunk_size = size
            self.update_chunk_size(size, self.set_plot_data)


        def set_transform():
            self.plot_data['wave']['is_on'] = False
            self.plot_data['stft']['is_on'] = False
            self.plot_data['mel']['is_on'] = False

            if mel_radio.isChecked():
                self.plot_data['mel']['is_on'] = True
                x_log_checkbox.setChecked(True)
                set_log()
            elif fft_radio.isChecked():
                self.plot_data['stft']['is_on'] = True
                x_log_checkbox.setChecked(True)
                set_log()
            elif wave_radio.isChecked():
                self.plot_data['wave']['is_on'] = True
                x_log_checkbox.setChecked(False)
                set_log()
                self.graph.setYRange(-.5, .5, padding=0)
                self.graph.setXRange(0, .086, padding=0)


        # Top Dock
        self.graph = pg.PlotWidget(self.win)
        self.graph.setBackground((0,0,0))
        self.graph.setLogMode(self.use_custom_log, False)
        reset_graph_scaling()
        self.plot = self.graph.plot(pen=pg.mkPen((255,255,0), width=2), skipFiniteCheck=True)

        self.top_dock = QDockWidget('GRAPH2D', widget=self.graph)
        self.win.addDockWidget(Qt.TopDockWidgetArea, self.top_dock)
        
        # Bottom Dock
        content_margins = QMargins(12, 12, 12, 12)

        presets_layout = QHBoxLayout()
        presets_layout.setContentsMargins(content_margins)
        presets_label = QLabel(text='Presets')
        presets_layout.addWidget(presets_label)
        presets_combobox = QComboBox()
        presets_combobox.addItems(['1024','2048','4096','8192'])
        presets_combobox.setCurrentIndex(2)
        presets_combobox.activated.connect(set_preset)
        presets_layout.addWidget(presets_combobox)

        hide_axis_layout = QHBoxLayout()
        hide_axis_layout.setContentsMargins(content_margins)
        hide_axis_label = QLabel(text='Hide Axis  ')
        hide_axis_layout.addWidget(hide_axis_label)
        hide_axis_checkbox = QCheckBox()
        hide_axis_checkbox.setChecked(False)
        hide_axis_checkbox.clicked.connect(set_hide_axis)
        hide_axis_layout.addWidget(hide_axis_checkbox)
        hide_axis_layout.addStretch()

        x_log_layout = QHBoxLayout()
        x_log_layout.setContentsMargins(content_margins)
        x_log_label = QLabel(text='Use X-Axis Log Scale  ')
        x_log_layout.addWidget(x_log_label)
        x_log_checkbox = QCheckBox()
        x_log_checkbox.setChecked(True)
        x_log_checkbox.clicked.connect(set_log)
        x_log_layout.addWidget(x_log_checkbox)
        x_log_layout.addStretch()

        y_height_layout = QVBoxLayout()
        y_height_layout.setContentsMargins(content_margins)
        y_height_label = QLabel(text='Y Height: ')
        y_height_layout.addWidget(y_height_label)
        y_height_slider = QSlider(Qt.Orientation.Horizontal)
        y_height_slider.setRange(0, 100)
        y_height_slider.setValue(20)
        y_height_slider.valueChanged.connect(set_height)
        y_height_layout.addWidget(y_height_slider)
        set_height()

        color_layout = QVBoxLayout()
        color_layout.setContentsMargins(content_margins)
        color_label = QLabel(text='Color Hue | Range')
        color_layout.addWidget(color_label)
        color_hue_slider = QSlider(Qt.Orientation.Horizontal)
        color_hue_slider.setValue(self.color_hue*100)
        color_hue_slider.setRange(0, 100)
        color_hue_slider.valueChanged.connect(set_color)
        color_layout.addWidget(color_hue_slider)
        color_range_slider = QSlider(Qt.Orientation.Horizontal)
        color_range_slider.setRange(0, 100)
        color_range_slider.setValue(self.color_range*10)
        color_range_slider.valueChanged.connect(set_color)
        color_layout.addWidget(color_range_slider)
        set_color()

        lerp_layout = QVBoxLayout()
        lerp_layout.setContentsMargins(content_margins)
        lerp_label = QLabel(text='Lerp Smoothing')
        lerp_layout.addWidget(lerp_label)
        lerp_slider = QSlider(Qt.Orientation.Horizontal)
        lerp_slider.setRange(0,99)
        lerp_slider.setValue(self.lerp_amount*100)
        lerp_slider.valueChanged.connect(set_lerp)
        lerp_layout.addWidget(lerp_slider)
        set_lerp()

        log_sigmoid_layout = QVBoxLayout()
        log_sigmoid_layout.setContentsMargins(content_margins)
        log_sigmoid_label = QLabel(text='Log/Sigmoid Ratio')
        log_sigmoid_layout.addWidget(log_sigmoid_label)
        log_sigmoid_slider = QSlider(Qt.Orientation.Horizontal)
        log_sigmoid_slider.setRange(0, 100)
        log_sigmoid_slider.setValue(self.sigmoid_amount*100)
        log_sigmoid_slider.valueChanged.connect(set_log_sigmoid)
        log_sigmoid_layout.addWidget(log_sigmoid_slider)
        set_log_sigmoid()

        sigmoid_options_layout = QVBoxLayout()
        sigmoid_options_layout.setContentsMargins(content_margins)
        sigmoid_options_label = QLabel(text='Sigmoid Limit | Gradient')
        sigmoid_options_layout.addWidget(sigmoid_options_label)
        sigmoid_limit_slider = QSlider(Qt.Orientation.Horizontal)
        sigmoid_limit_slider.setRange(0, 100)
        sigmoid_limit_slider.setValue(self.sigmoid_limit)
        sigmoid_limit_slider.valueChanged.connect(set_sigmoid_options)
        sigmoid_options_layout.addWidget(sigmoid_limit_slider)
        sigmoid_gradient_slider = QSlider(Qt.Orientation.Horizontal)
        sigmoid_gradient_slider.setRange(0, 100)
        sigmoid_gradient_slider.setValue(self.sigmoid_gradient*100)
        sigmoid_gradient_slider.valueChanged.connect(set_sigmoid_options)
        sigmoid_options_layout.addWidget(sigmoid_gradient_slider)
        set_sigmoid_options()

        chunk_layout = QHBoxLayout()
        chunk_layout.setContentsMargins(content_margins)
        chunk_label = QLabel(text='Chunk Size (Only 2048 and 4096 are recommended)')
        chunk_layout.addWidget(chunk_label)
        chunk_combobox = QComboBox()
        chunk_combobox.addItems(['1024','2048','4096','8192'])
        chunk_combobox.setCurrentIndex(2)
        chunk_combobox.activated.connect(set_chunk_size)
        chunk_layout.addWidget(chunk_combobox)

        transform_layout = QVBoxLayout()
        transform_layout.setContentsMargins(content_margins)
        transform_label = QLabel(text='Transform Type')
        transform_layout.addWidget(transform_label)
        mel_radio = QRadioButton(text='Mel', checked=True)
        transform_layout.addWidget(mel_radio)
        mel_radio.clicked.connect(set_transform)
        fft_radio = QRadioButton(text='STFT')
        fft_radio.clicked.connect(set_transform)
        transform_layout.addWidget(fft_radio)
        wave_radio = QRadioButton(text='Wave')
        transform_layout.addWidget(wave_radio)
        wave_radio.clicked.connect(set_transform)

        # Create scrolling frame
        settings_scroll = QScrollArea(widgetResizable=True)
        settings_layout = QVBoxLayout()
        playlists_box_widget = QFrame(settings_scroll, layout=settings_layout)
        settings_scroll.setWidget(playlists_box_widget)

        # Merge layouts
        settings_layout.addLayout(presets_layout)
        settings_layout.addLayout(hide_axis_layout)
        settings_layout.addLayout(x_log_layout)
        settings_layout.addLayout(y_height_layout)
        settings_layout.addLayout(color_layout)
        settings_layout.addLayout(lerp_layout)
        settings_layout.addLayout(log_sigmoid_layout)
        settings_layout.addLayout(sigmoid_options_layout)
        settings_layout.addLayout(chunk_layout)
        settings_layout.addLayout(transform_layout)

        # Add to dock
        self.bottom_dock = QDockWidget('GRAPH2D', widget=settings_scroll)
        self.win.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.bottom_dock)


    def set_plot_data(self, keep=False):
        self.plot_data['wave'].update({
            'x': np.arange(self.chunk_size)/self.sr,
            'y': np.zeros(self.chunk_size, np.float32),
            'visual_x': np.arange(self.chunk_size)/self.sr,
            'visual_y': np.zeros(self.chunk_size, np.float32)
        })
        self.plot_data['stft'].update({
            'n': self.chunk_size,
            'x': 0,
            'y': 0,
            'visual_x': 0,
            'visual_y': 0
        })
        self.plot_data['mel'].update({
            'n': self.chunk_size//8,
            'x': 0,
            'y': 0,
            'visual_x': 0,
            'visual_y': 0,
            'filter': 0
        })

        pd = self.plot_data

        if not keep:
            self.plot_data['wave']['is_on'] = False
            self.plot_data['stft']['is_on'] = False
            self.plot_data['mel']['is_on'] = True

        self.plot_data['stft']['x'] = librosa.fft_frequencies(sr=self.sr, n_fft=self.plot_data['stft']['n'])
        self.plot_data['mel']['x'] = librosa.mel_frequencies(n_mels=self.plot_data['mel']['n'], fmax=self.sr/2)

        self.plot_data['stft']['visual_x'] = self.plot_data['stft']['x']
        self.plot_data['mel']['visual_x'] = self.plot_data['mel']['x']

        self.plot_data['stft']['y'] = np.abs(librosa.stft(y=pd['wave']['y'], n_fft=pd['stft']['n'], hop_length=pd['stft']['n']*2, center=False)).flatten()
        self.plot_data['mel']['y'] = librosa.feature.melspectrogram(y=pd['wave']['y'], n_fft=pd['stft']['n'], hop_length=pd['stft']['n'], center=False, n_mels=pd['mel']['n'], sr=self.sr).flatten()

        self.plot_data['stft']['visual_y'] = self.plot_data['stft']['y']
        self.plot_data['mel']['visual_y'] = self.plot_data['mel']['y']
        # self.plot_data['mel']['filter'] = librosa.filters.mel(sr=self.sr, n_fft=self.chunk_size//2, fmax=self.sr/2),


    def update_plot(self):
        for trace_name in self.plot_data:
            trace = self.plot_data[trace_name]
            if trace['is_on']:
                trace['visual_x'] = self.lerp(trace['visual_x'], trace['x'], 1-self.lerp_amount)
                trace['visual_y'] = self.lerp(trace['visual_y'], trace['y'], 1-self.lerp_amount)
                if trace_name == 'wave':
                    y = trace['visual_y']
                    strength = self.color_hue+np.average(np.abs(trace['visual_y']))*self.color_range/20
                else:
                    y = (np.log(trace['visual_y']+0.000001)+1)*(1-self.sigmoid_amount) + self.sigmoid(
                        trace['visual_y'], self.sigmoid_limit, self.sigmoid_gradient)*self.sigmoid_amount
                    strength = self.color_hue+np.average(trace['visual_y'])*self.color_range*(4096/self.chunk_size)*np.abs(self.average_amp)/500
                color = [x*255 for x in colorsys.hsv_to_rgb(strength, 1, 1)]
                self.plot.setData(trace['visual_x'], y, pen=pg.mkPen(color, width=2))


    def update_data(self, indata, average_amp):
        self.average_amp = average_amp
        pd = self.plot_data

        if indata.shape[1] == 2:
            pd['wave']['y'] = np.array((indata[:,0] + indata[:,1])/2, dtype='float32')
        else:
            pd['wave']['y'] = indata.flatten()
    
        if pd['stft']['is_on']: 
            pd['stft']['y'] = np.abs(librosa.stft(y=pd['wave']['y'], n_fft=pd['stft']['n'], hop_length=pd['stft']['n']*2, center=False)).flatten()
        if pd['mel']['is_on']:
            pd['mel']['y'] = librosa.feature.melspectrogram(y=pd['wave']['y'], n_fft=pd['stft']['n'], hop_length=pd['stft']['n'], center=False, n_mels=pd['mel']['n'], sr=self.sr).flatten()


    def export(self, i):
        exporter = pyqtgraph.exporters.ImageExporter(self.graph.plotItem)
        exporter.export(str(self.PATH/'tmp'/'vid'/(str(i)+'.jpg')))

        
    def sigmoid(self, a, limit, gradient):
        return limit*2/(1 + np.exp(-a*gradient)) - limit
        

    def lerp(self, a, b, amount):
        return a + (b-a) * amount
