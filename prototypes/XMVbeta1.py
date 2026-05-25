import os
import sys
import time
import numpy as np
import librosa
import sounddevice as sd
import soundfile as sf
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QComboBox, QDockWidget, QWidget, QTabWidget, QMenuBar, QListWidget
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont, QFontDatabase, QPixmap
import pyqtgraph as pg  # import order MATTERS (putting pyqtgraph before pyside will fail)
import colorsys

class xmv():
    def __init__(self):
        self.PATH = os.path.dirname(os.path.realpath(__file__))

        # Window and app
        pg.setConfigOptions(useOpenGL=True, antialias=True)
        self.app = QApplication(sys.argv)
        self.fonts = self.import_fonts([
            f'{self.PATH}/res/fonts/moongloss/MoonGlossDisplayThick.otf',
            f'{self.PATH}/res/fonts/nova_square/NovaSquare-Book.ttf',
            f'{self.PATH}/res/fonts/sans_mateo/Sans Mateo 2 Regular.ttf'
        ])
        self.app.setFont(QFont(self.fonts['moongloss'][0], 16))
        self.win = QMainWindow()
        self.win.setWindowTitle('XMV')
        self.win.setGeometry(0, 0, 1500, 1000)
        self.win.setStyleSheet("* {background-color: #111111; color: white;} QTabBar:tab {background-color: #222222;}")

        # Global Variables
        self.gb = self.create_globals()
        self.read_file(self.gb['file_path'], self.gb['chunk_size'])
        self.gb['plot_data'] = self.create_plot_data(self.gb['chunk_size'], self.gb['sr'])

        # Layout
        self.create_layout()      

        # Stream
        self.stream = sd.Stream(samplerate=self.gb['sr'], blocksize=self.gb['chunk_size'], dtype=np.float32, channels=self.gb['channels'], callback=self.callback, latency=0)
        
        # Animation timer
        self.timer = QTimer(self.win)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(10)

        # self.win.showFullScreen()
        self.win.showMaximized()


    def import_fonts(self, paths):
        fonts = {}
        for path in paths:
            font_name = path.split('/')[-2]
            font_id = QFontDatabase.addApplicationFont(path)
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            fonts[font_name] = font_families
        return fonts


    def create_layout(self):
        gb = self.gb

        # Menubar
        menu_layout = QHBoxLayout()
        menu_layout.setContentsMargins(12,12,12,12)
        menu_layout.setAlignment(Qt.AlignHCenter)
        menu_layout.setSpacing(10)

        menu_logo = QPixmap(f"{self.PATH}/res/images/xmv_logo_x32.webp")
        menu_logo_label = QLabel()
        menu_logo_label.setPixmap(menu_logo)
        menu_layout.addWidget(menu_logo_label)
        
        menu_title = QLabel(text='XzistMusicVisualizer')
        menu_title.setFont(QFont(self.fonts['sans_mateo'][0], 24))
        menu_layout.addWidget(menu_title)

        menu_layout.addStretch(1)


        def fullscreen_toggle():
            if self.win.windowState() != Qt.WindowFullScreen:
                self.win.setWindowState(Qt.WindowFullScreen)
            else:
                self.win.setWindowState(Qt.WindowNoState)


        menu_fullscreen_button = QPushButton(text='FULLSCREEN')
        menu_fullscreen_button.pressed.connect(fullscreen_toggle)
        menu_layout.addWidget(menu_fullscreen_button)

        menu_widget = QWidget()
        menu_widget.setLayout(menu_layout)
        menu_widget.setStyleSheet("background: #050505; color: white;")
        
        menu_seperation_layout = QVBoxLayout()
        menu_seperation_layout.setContentsMargins(0,0,0,10)
        menu_seperation_layout.addWidget(menu_widget)

        menu_seperation_widget = QWidget()
        menu_seperation_widget.setLayout(menu_seperation_layout)

        self.win.setMenuWidget(menu_seperation_widget)

        # Graph Plot
        self.graph = pg.PlotWidget(self.win)
        self.graph.setBackground((0,0,0))
        self.graph.disableAutoRange()
        self.graph.setLogMode(gb['use_custom_log']['x'], gb['use_custom_log']['y'])
        self.graph.setYRange(15, 60, padding=0)
        self.graph.setXRange(1.1, 4.4, padding=0)
        self.plt = self.graph.plot(pen=pg.mkPen((255,255,0), width=2), skipFiniteCheck=True)

        self.plot_dock = QDockWidget('GRAPH')
        self.plot_dock.setWidget(self.graph)
        self.win.addDockWidget(Qt.TopDockWidgetArea, self.plot_dock)

        # Empty QWidget Hack
        self.win.setCentralWidget(QWidget())

        # Settings
        settings_layout = QVBoxLayout()

        button = QPushButton(text='PUCH')
        settings_layout.addWidget(button)

        button2 = QPushButton(text='PUCH2')
        settings_layout.addWidget(button2)

        settings_widget = QWidget()
        settings_widget.setLayout(settings_layout)
        self.settings_dock = QDockWidget('SETTINGS')
        self.settings_dock.setWidget(settings_widget)
        self.win.addDockWidget(Qt.BottomDockWidgetArea, self.settings_dock)

        # Playback
        def select_audio():
            gb['playlist_index'] = self.playlist.currentRow()
            gb['file_path'] = gb['playlist_files'][gb['playlist_index']]
            gb['audio_frame'] = 0
            self.read_file(gb['playlist_folder_path']+gb['file_path'], gb['chunk_size'])
            self.playback_slider.setRange(0, gb['chunk_count'])


        
        self.playlist = QListWidget()
        self.playlist.addItems(gb['playlist_files'])
        self.playlist.pressed.connect(select_audio)

        playback_layout = QHBoxLayout()


        def set_playback():
            gb['audio_frame'] = self.playback_slider.value()
            if gb['audio_frame'] >= gb['chunk_count']:
                self.play_button.setText('||')
                gb['is_playing_file'] = True


        self.playback_slider = QSlider(Qt.Orientation.Horizontal)
        self.playback_slider.setRange(0, gb['chunk_count'])
        self.playback_slider.valueChanged.connect(set_playback)
        playback_layout.addWidget(self.playback_slider)


        def set_volume():
            gb['volume'] = volume_slider.value()/500


        volume_slider = QSlider(Qt.Orientation.Horizontal)
        volume_slider.setRange(0, 100)
        volume_slider.setFixedWidth(100)
        volume_slider.setValue(gb['volume']*500)
        volume_slider.valueChanged.connect(set_volume)
        playback_layout.addWidget(volume_slider)

        # Playback buttons
        playback_buttons_layout = QHBoxLayout()


        def back_seek():
            gb['playlist_index'] = (gb['playlist_index']-1) % len(gb['file_path'])
            gb['file_path'] = gb['playlist_files'][gb['playlist_index']]
            gb['audio_frame'] = 0
            self.read_file(gb['playlist_folder_path']+gb['file_path'], gb['chunk_size'])
            self.playback_slider.setRange(0, gb['chunk_count'])


        self.back_button = QPushButton(text='<')
        self.back_button.pressed.connect(back_seek)
        playback_buttons_layout.addWidget(self.back_button)


        def play_toggle():
            if gb['is_playing_file']:
                self.play_button.setText('>')
                gb['is_playing_file'] = False
            else:
                self.play_button.setText('||')
                gb['is_playing_file'] = True
                if gb['audio_frame'] >= gb['chunk_count']:
                    self.playback_slider.setValue(0)
                    set_playback()


        self.play_button = QPushButton(text='||')
        self.play_button.pressed.connect(play_toggle)
        playback_buttons_layout.addWidget(self.play_button)


        def forward_seek():
            gb['playlist_index'] = (gb['playlist_index']+1) % len(gb['file_path'])
            gb['file_path'] = gb['playlist_files'][gb['playlist_index']]
            gb['audio_frame'] = 0
            self.read_file(gb['playlist_folder_path']+gb['file_path'], gb['chunk_size'])
            self.playback_slider.setRange(0, gb['chunk_count'])


        self.forward_button = QPushButton(text='>')
        self.forward_button.pressed.connect(forward_seek)
        playback_buttons_layout.addWidget(self.forward_button)
        

        playback_widget = QWidget()
        playback_widget.setLayout(playback_layout)
        playback_buttons_widget = QWidget()
        playback_buttons_widget.setLayout(playback_buttons_layout)

        playback_box_layout = QVBoxLayout()
        playback_box_layout.addWidget(self.playlist)
        playback_box_layout.addWidget(playback_widget)
        playback_box_layout.addWidget(playback_buttons_widget)
        playback_box_widget = QWidget()
        playback_box_widget.setLayout(playback_box_layout)
        playback_box_widget.setContentsMargins(2,2,2,2)
        
        self.playback_dock = QDockWidget('PLAYBACK')
        self.playback_dock.setWidget(playback_box_widget)
        self.win.addDockWidget(Qt.BottomDockWidgetArea, self.playback_dock)
        self.win.tabifyDockWidget(self.settings_dock, self.playback_dock)


        self.win.setTabPosition(Qt.AllDockWidgetAreas, QTabWidget.North)
        self.win.resizeDocks([self.plot_dock, self.settings_dock], [450, 500], Qt.Vertical)


    def sigmoid(self, a, scale=100):
        return scale/(1 + np.exp(-a/100)) - 0.5
        

    def lerp(self, a, b, amount):
        return a + (b-a) * amount


    def update_data(self, indata):
        pd = self.gb['plot_data']

        if indata.shape[1] == 2:
            pd['wave']['y'] = np.array((indata[:,0] + indata[:,1])/2, dtype='float32')
        else:
            pd['wave']['y'] = indata.flatten()
    
        if pd['stft']['is_on']:
            pd['stft']['y'] = np.abs(librosa.stft(y=pd['wave']['y'], n_fft=pd['stft']['n'], hop_length=pd['stft']['n']*2, center=False)).flatten()
        if pd['fmt']['is_on']:
            pd['fmt']['y'] = librosa.feature.melspectrogram(y=pd['wave']['y'], n_fft=pd['stft']['n'], hop_length=pd['stft']['n'], center=False, n_mels=pd['fmt']['n'], sr=self.gb['sr']).flatten()


    def callback(self, indata, outdata, frames, time, status):
        gb = self.gb
        total_data = np.zeros((gb['chunk_size'], indata.shape[1]), dtype=np.float32)
        
        if gb['is_playing_file']:
            if gb['audio_frame'] >= gb['chunk_count']:
                
                gb['playlist_index'] = (gb['playlist_index']+1) % len(gb['file_path'])
                gb['file_path'] = gb['playlist_files'][gb['playlist_index']]
                gb['audio_frame'] = 0
                self.read_file(gb['playlist_folder_path']+gb['file_path'], gb['chunk_size'])
                self.playback_slider.setRange(0, gb['chunk_count'])


                # self.gb['is_playing_file'] = False
                # self.play_button.setText('>')
                return
            
            outdata[:gb['chunk_size']] = gb['file_data_chunks'][gb['audio_frame']]*gb['volume']  # interesting I can't set it directly but i have to add [:chunk_size] 
            total_data += gb['file_data_chunks'][gb['audio_frame']]

            gb['audio_frame'] += 1
            self.playback_slider.setValue(gb['audio_frame'])
        else:
            outdata[:gb['chunk_size']] = 0

        if gb['is_use_mic']:
            total_data += indata

        self.update_data(total_data)


    def update_plot(self):
        for trace_name in self.gb['plot_data']:
            trace = self.gb['plot_data'][trace_name]
            if trace['is_on']:
                trace['visual_x'] = self.lerp(trace['visual_x'], trace['x'], self.gb['lerp_amount'])
                trace['visual_y'] = self.lerp(trace['visual_y'], trace['y'], self.gb['lerp_amount'])
                y = (np.log(trace['visual_y']+0.0000001) + self.sigmoid(trace['visual_y']))/2
                strength = np.average(trace['visual_y'])/120
                color = [x*255 for x in colorsys.hsv_to_rgb(0.75+strength, 1, 1)]

                self.plt.setData(trace['visual_x'], y, pen=pg.mkPen(color, width=2))
        

    def create_plot_data(self, chunk_size, sr):
        data = {
            'wave': {
                'x': np.arange(chunk_size)/sr,
                'y': np.zeros(chunk_size, np.float32),
                'visual_x': np.arange(chunk_size)/sr,
                'visual_y': np.zeros(chunk_size, np.float32),
                'is_on': False
            },
            'stft': {
                'n': chunk_size,
                'x': 0,
                'y': 0,
                'visual_x': 0,
                'visual_y': 0,
                'is_on': False
            },
            'fmt': {
                'n': chunk_size//8,
                'x': 0,
                'y': 0,
                'visual_x': 0,
                'visual_y': 0,
                'filter': 0,
                'is_on': True
            }
        }

        data['stft']['x'] = librosa.fft_frequencies(sr=sr, n_fft=data['stft']['n'])
        data['fmt']['x'] = librosa.mel_frequencies(n_mels=data['fmt']['n'], fmax=sr/2)

        data['stft']['visual_x'] = data['stft']['x']
        data['fmt']['visual_x'] = data['fmt']['x']

        data['stft']['y'] = np.zeros(len(data['stft']['x']), np.float32)
        data['fmt']['y'] = np.zeros(len(data['fmt']['x']), np.float32)

        data['stft']['visual_y'] = data['stft']['y']
        data['fmt']['visual_y'] = data['fmt']['y']

        data['fmt']['filter'] = librosa.filters.mel(sr=sr, n_fft=2048, fmax=sr/2),

        return data


    def read_file(self, file_path, chunk_size):
        if os.path.exists(file_path):
            file_data, sr = sf.read(file_path, dtype=np.float32)
            chunk_count = len(file_data)//chunk_size+1
            channels = file_data.shape[1]
            
            file_data_chunks = np.zeros((chunk_count, chunk_size, channels), np.float32)
            for i in range(0, chunk_count-1):
                file_data_chunks[i] = file_data[chunk_size*(i):chunk_size*(i+1)]
            file_data_chunks[-1] = np.resize(file_data[chunk_size*(chunk_count-1):], (chunk_size, channels))

            self.gb['file_data_chunks'] = file_data_chunks
            self.gb['file_data'] = file_data
            self.gb['sr'] = sr
            self.gb['chunk_count'] = chunk_count
            self.gb['channels'] = channels


    def create_globals(self):
        sr = 48000
        chunk_size = 4096
        channels = 2
        lerp_amount = 1/4
        use_custom_log = {'x': True, 'y': False}
        log_base = (10,2)
        playlist_folder_path = f'{self.PATH}/audio/'
        playlist_files = os.listdir(f'{self.PATH}/audio')
        playlist_index = 0
        file_path = playlist_folder_path + playlist_files[playlist_index]
        volume = 0.1
        audio_frame = 0

        is_playing_file = True
        is_use_mic = False
        file_data_chunks, file_data, chunk_count = None, None, None

        plot_data = 0

        fps = 120
        time_scale = 1/fps
        
        return {
            'sr': sr,
            'chunk_size': chunk_size,
            'channels': channels,
            'lerp_amount': lerp_amount,
            'use_custom_log': use_custom_log,
            'log_base': log_base,
            'playlist_folder_path': playlist_folder_path,
            'playlist_files': playlist_files,
            'playlist_index': playlist_index,
            'file_path': file_path,
            'volume': volume,
            'audio_frame': audio_frame,
            'is_playing_file': is_playing_file,
            'is_use_mic': is_use_mic,
            'file_data_chunks': file_data_chunks,
            'file_data': file_data,
            'chunk_count': chunk_count,
            'fps': fps,
            'time_scale': time_scale,
            'plot_data': plot_data
        }


    def run(self):
        if (sys.flags.interactive != 1) or not hasattr(pg.QtCore, 'PYQT_VERSION'):
            with self.stream:
                self.app.instance().exec()


if __name__ == '__main__':
    xmv().run()