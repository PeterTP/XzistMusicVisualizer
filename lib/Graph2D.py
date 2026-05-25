from PySide6.QtWidgets import QDockWidget, QGridLayout, QVBoxLayout, QLabel, QWidget, QSpinBox, QSlider, QRadioButton, QComboBox
from PySide6.QtCore import Qt
import pyqtgraph as pg  # import order MATTERS (putting pyqtgraph before pyside will fail)
import numpy as np
import librosa
import colorsys


class Graph2D:
    def __init__(self, win):
        self.win = win

        self.sr = 48000
        self.chunk_size = 4096
        self.lerp_amount = 1/3
        self.use_custom_log = {'x': True, 'y': False}
        self.log_base = (10,2)

        self.fps = 120
        self.time_scale = 1/self.fps

        pg.setConfigOptions(useOpenGL=True, antialias=True)
        self.set_plot_data()
        self.create_docks()
        

    def create_docks(self):
        # Top Dock
        self.graph = pg.PlotWidget(self.win)
        self.graph.setBackground((0,0,0))
        self.graph.disableAutoRange()
        self.graph.setLogMode(self.use_custom_log['x'], self.use_custom_log['y'])
        self.graph.setYRange(15, 60, padding=0)
        self.graph.setXRange(1.1, 4.4, padding=0)
        self.plot = self.graph.plot(pen=pg.mkPen((255,255,0), width=2), skipFiniteCheck=True)

        self.top_dock = QDockWidget('GRAPH2D', widget=self.graph)
        self.win.addDockWidget(Qt.TopDockWidgetArea, self.top_dock)
        
        # Bottom Dock
        x_scale_layout = QVBoxLayout()
        x_scale_label = QLabel(text='X-Axis Scale')
        x_scale_layout.addWidget(x_scale_label)
        x_scale_spinbox = QSpinBox()
        x_scale_layout.addWidget(x_scale_spinbox)

        lerp_layout = QVBoxLayout()
        lerp_label = QLabel(text='Lerp Smoothing')
        lerp_layout.addWidget(lerp_label)
        lerp_slider = QSlider(Qt.Orientation.Horizontal)
        lerp_layout.addWidget(lerp_slider)

        color_layout = QVBoxLayout()
        color_label = QLabel(text='Color Limit')
        color_layout.addWidget(color_label)
        color_min_slider = QSlider(Qt.Orientation.Horizontal)
        color_layout.addWidget(color_min_slider)
        color_max_slider = QSlider(Qt.Orientation.Horizontal)
        color_layout.addWidget(color_max_slider)

        chunk_layout = QVBoxLayout()
        chunk_label = QLabel(text='Chunk Size')
        chunk_layout.addWidget(chunk_label)
        chunk_combobox = QComboBox()
        chunk_layout.addWidget(chunk_combobox)

        sigmoid_layout = QVBoxLayout()
        sigmoid_label = QLabel(text='Sigmoid/Log Ratio')
        sigmoid_layout.addWidget(sigmoid_label)
        sigmoid_slider = QSlider(Qt.Orientation.Horizontal)
        sigmoid_layout.addWidget(sigmoid_slider)

        transform_layout = QVBoxLayout()
        transform_label = QLabel(text='Transform Type')
        transform_layout.addWidget(transform_label)
        fft_radio = QRadioButton(text='FFT')
        transform_layout.addWidget(fft_radio)
        fmt_radio = QRadioButton(text='FMT')
        transform_layout.addWidget(fmt_radio)
        cqt_radio = QRadioButton(text='CQT')
        transform_layout.addWidget(cqt_radio)

        # Merge widget and layouts
        settings_layout = QGridLayout()
        settings_layout.addLayout(x_scale_layout, 0, 0, Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        settings_layout.addLayout(lerp_layout, 0, 1, Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        settings_layout.addLayout(color_layout, 0, 2, Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        settings_layout.addLayout(chunk_layout, 1, 0, Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        settings_layout.addLayout(sigmoid_layout, 1, 1, Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        settings_layout.addLayout(transform_layout, 1, 2, Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        for i in range(settings_layout.columnCount()): settings_layout.setColumnStretch(i, 1)
        playlists_box_widget = QWidget(layout=settings_layout)

        self.bottom_dock = QDockWidget('GRAPH2D', widget=playlists_box_widget)
        self.win.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.bottom_dock)


    def set_plot_data(self):
        self.plot_data = {
            'wave': {
                'x': np.arange(self.chunk_size)/self.sr,
                'y': np.zeros(self.chunk_size, np.float32),
                'visual_x': np.arange(self.chunk_size)/self.sr,
                'visual_y': np.zeros(self.chunk_size, np.float32),
                'is_on': False
            },
            'stft': {
                'n': self.chunk_size,
                'x': 0,
                'y': 0,
                'visual_x': 0,
                'visual_y': 0,
                'is_on': False
            },
            'fmt': {
                'n': self.chunk_size//8,
                'x': 0,
                'y': 0,
                'visual_x': 0,
                'visual_y': 0,
                'filter': 0,
                'is_on': True
            }
        }

        self.plot_data['stft']['x'] = librosa.fft_frequencies(sr=self.sr, n_fft=self.plot_data['stft']['n'])
        self.plot_data['fmt']['x'] = librosa.mel_frequencies(n_mels=self.plot_data['fmt']['n'], fmax=self.sr/2)

        self.plot_data['stft']['visual_x'] = self.plot_data['stft']['x']
        self.plot_data['fmt']['visual_x'] = self.plot_data['fmt']['x']

        self.plot_data['stft']['y'] = np.zeros(len(self.plot_data['stft']['x']), np.float32)
        self.plot_data['fmt']['y'] = np.zeros(len(self.plot_data['fmt']['x']), np.float32)

        self.plot_data['stft']['visual_y'] = self.plot_data['stft']['y']
        self.plot_data['fmt']['visual_y'] = self.plot_data['fmt']['y']

        self.plot_data['fmt']['filter'] = librosa.filters.mel(sr=self.sr, n_fft=2048, fmax=self.sr/2),


    def update_plot(self):
        for trace_name in self.plot_data:
            trace = self.plot_data[trace_name]
            if trace['is_on']:
                trace['visual_x'] = self.lerp(trace['visual_x'], trace['x'], self.lerp_amount)
                trace['visual_y'] = self.lerp(trace['visual_y'], trace['y'], self.lerp_amount)
                y = (np.log(trace['visual_y']+0.000001) + self.sigmoid(trace['visual_y']))/2
                strength = np.average(trace['visual_y'])/500
                color = [x*255 for x in colorsys.hsv_to_rgb(0.75+strength, 1, 1)]

                self.plot.setData(trace['visual_x'], y, pen=pg.mkPen(color, width=2))


    def update_data(self, indata):
        pd = self.plot_data

        if indata.shape[1] == 2:
            pd['wave']['y'] = np.array((indata[:,0] + indata[:,1])/2, dtype='float32')
        else:
            pd['wave']['y'] = indata.flatten()
    
        if pd['stft']['is_on']:
            pd['stft']['y'] = np.abs(librosa.stft(y=pd['wave']['y'], n_fft=pd['stft']['n'], hop_length=pd['stft']['n']*2, center=False)).flatten()
        if pd['fmt']['is_on']:
            pd['fmt']['y'] = librosa.feature.melspectrogram(y=pd['wave']['y'], n_fft=pd['stft']['n'], hop_length=pd['stft']['n'], center=False, n_mels=pd['fmt']['n'], sr=self.sr).flatten()


    def sigmoid(self, a, scale=100):
        return scale/(1 + np.exp(-a/100)) - 0.5
        

    def lerp(self, a, b, amount):
        return a + (b-a) * amount