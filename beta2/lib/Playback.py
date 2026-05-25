from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QDockWidget, QWidget, QListWidget, QCheckBox, QLabel, QStyledItemDelegate, QStyleOptionSlider, QStyle
from PySide6.QtCore import Qt
import json
import random
from pathlib import Path
import numpy as np
import sounddevice as sd
import soundfile as sf
import pyloudnorm as pyln
from librosa import stft
from lib.GetPlaylistInfo import GetPlaylistInfo


class Playback:
    def __init__(self, win, PATH, update_plots, download):
        self.win = win
        self.PATH = PATH
        self.update_plots = update_plots
        self.download = download

        self.sr = 48000
        self.channels = 2
        self.chunk_size = 4096
        self.file_data = np.zeros(0)
        self.data_chunks = np.zeros(0)
        self.chunk_count = 0

        self.is_playing = True
        self.frame = 0
        self.audio_avg = 1

        self.stream = sd.Stream(samplerate=self.sr, blocksize=self.chunk_size, dtype=np.float32, channels=self.channels, callback=self.callback, latency='low')

        self.create_dock()
        self.update_playlist()

    
    def create_dock(self):
        def select_playlist():
            if self.playlists_list.currentItem().text() != self.playlists_data['Playlists']['current']:
                self.update_playlist(self.playlists_list.currentItem().text())
                # self.playlists_list.selectedItems=[self.playlists_list.currentItem()] TODO


        def select_audio():
            self.playlist_index = self.playlist.currentRow()
            self.set_audio()


        def set_playback():
            self.frame = self.playback_slider.value()


        def set_volume():
            self.settings_data['volume'] = self.volume_slider.value()/100


        def toggle_shuffle():
            copied_list = list(self.current_playlist_data['items'].copy())
            if shuffle_checkbox.isChecked():
                random.shuffle(copied_list)
                self.playlist.clear()
                self.playlist.addItems(copied_list) 
            else:
                self.playlist.clear()
                self.playlist.addItems(copied_list)

            self.playlist.setCurrentRow(self.playlist_index)
            self.playing_label.setText(f'Playing: {self.playlist_index+1}. {self.playlist.currentItem().text()}')


        # Playlists
        self.playlists_list = QListWidget(flow=QListWidget.Flow.LeftToRight, spacing=4)
        self.playlists_list.setMinimumHeight(50)
        self.playlists_list.clicked.connect(select_playlist)

        # Playlist
        self.playlist = QListWidget()
        delegate = Delegate(self.playlist)
        self.playlist.setItemDelegate(delegate)
        self.playlist.clicked.connect(select_audio)

        # Playing
        self.playing_label = QLabel("Playing: ")

        # Playback seek and volume sliders
        playback_layout = QHBoxLayout()

        self.playback_slider = Slider(Qt.Orientation.Horizontal)
        self.playback_slider.setRange(0, self.chunk_count)
        self.playback_slider.valueChanged.connect(set_playback)
        playback_layout.addWidget(self.playback_slider)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(set_volume)
        self.volume_slider.sliderReleased.connect(self.save_data)
        playback_layout.addWidget(self.volume_slider)

        # Buttons
        playback_buttons_layout = QHBoxLayout()
        playback_buttons_layout.setContentsMargins(0,5,0,5)

        back_button = QPushButton()
        back_button.setContentsMargins(0,10,0,10)
        back_button_icon = QPixmap(f"{self.PATH}/res/images/left-control-button-icooon-white.webp")
        back_button.setIcon(back_button_icon)
        back_button.clicked.connect(lambda: self.seek(-1))
        playback_buttons_layout.addWidget(back_button)

        self.play_button = QPushButton()
        self.play_button.setContentsMargins(0,10,0,10)
        play_button_icon = QPixmap(f"{self.PATH}/res/images/pause-button-icooon-white.webp")
        self.play_button.setIcon(play_button_icon)
        self.play_button.clicked.connect(self.play_toggle)
        playback_buttons_layout.addWidget(self.play_button)

        forward_button = QPushButton()
        forward_button.setContentsMargins(0,10,0,10)
        forward_button_icon = QPixmap(f"{self.PATH}/res/images/right-control-button-icooon-white.webp")
        forward_button.setIcon(forward_button_icon)
        forward_button.clicked.connect(lambda: self.seek(1))
        playback_buttons_layout.addWidget(forward_button)

        shuffle_checkbox = QCheckBox()
        shuffle_checkbox_icon = QPixmap(f"{self.PATH}/res/images/shuffle-1-icooon-white.webp")
        shuffle_checkbox.setIcon(shuffle_checkbox_icon)
        shuffle_checkbox.clicked.connect(toggle_shuffle)
        playback_buttons_layout.addWidget(shuffle_checkbox)

        # Merge widget and layouts
        playback_box_layout = QVBoxLayout()
        playback_box_layout.addWidget(self.playlists_list, 1)
        playback_box_layout.addWidget(self.playlist, 6)
        playback_box_layout.addWidget(self.playing_label, 1)
        playback_box_layout.addLayout(playback_layout)
        playback_box_layout.addLayout(playback_buttons_layout)
        playback_box_widget = QWidget(layout=playback_box_layout)
        playback_box_widget.setContentsMargins(2,2,2,2)

        self.dock = QDockWidget('PLAYBACK', widget=playback_box_widget)
        self.win.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dock)


    def update_playlist(self, set_playlist=None):
        def update_items(info, set=False):
            if set:
                self.current_playlist_data['items'].clear()

            self.current_playlist_data['items'].update(info)
            self.playlist.clear()
            self.playlist.addItems(list(self.current_playlist_data['items']))


        def update_complete(date):
            self.current_playlist_data['last_updated'] = str(date)
            self.save_data()


        self.is_playing = False

        self.playlist_index = 0
        self.playlists_list.clear()
        self.playlist.clear()

        with open(self.PATH/'res'/'data.json', 'r', encoding='utf-8') as f:
            self.playlists_data = json.load(f)

        if set_playlist:
            self.playlists_data['Playlists']['current'] = set_playlist

        self.current_playlist_data = self.playlists_data['Playlists']['lists'][self.playlists_data['Playlists']['current']]
        self.settings_data = self.playlists_data['Playback']
        self.playlists_list.addItems(list(self.playlists_data['Playlists']['lists']))

        for i in range(self.playlists_list.count()):
            if self.playlists_list.item(i).text() == self.playlists_data['Playlists']['current']:
                self.playlists_list.setCurrentRow(i)
                break

        if self.current_playlist_data['type'] == 'local':
            # self.current_playlist_data['items'] will hold local file paths
            for item in Path(self.current_playlist_data['path']).iterdir():
                name = item.stem
                self.playlist.addItem(name)
                self.current_playlist_data['items'][name] = str(item)
            
        else:
            # self.current_playlist_data['items'] will hold urls
            GetPlaylistInfo().get_playlist_info(self.current_playlist_data['path'], update_items, update_complete, cache_last_updated=self.current_playlist_data['last_updated'])
            self.playlist.addItems(list(self.current_playlist_data['items']))

        self.volume_slider.setValue(self.settings_data['volume']*100)
        self.set_audio()
        self.save_data()


    def save_data(self):
        self.playlists_data['Playlists']['lists'][self.playlists_data['Playlists']['current']] = self.current_playlist_data
        self.playlists_data['Playback'] = self.settings_data

        with open(self.PATH/'res'/'data.json', 'w', encoding='utf-8') as f:
            json.dump(self.playlists_data, f, ensure_ascii=False, indent=4)


    def read_audio_file(self, reset=True):
        try:
            if self.file_path.exists():
                self.file_data, self.sr = sf.read(self.file_path, dtype=np.float32)

                # Normalize audio and get average
                meter = pyln.Meter(self.sr)
                loudness = meter.integrated_loudness(self.file_data)
                self.file_data = pyln.normalize.loudness(self.file_data, loudness, -14.0)
                self.audio_avg = np.average(np.abs(stft(y=self.file_data.flatten(), n_fft=4096, hop_length=4096*2, center=False)).flatten())
                self.chunk_count = len(self.file_data)//self.chunk_size+1
                self.channels = self.file_data.shape[1]

                # Split file data into chunks
                self.data_chunks = np.zeros((self.chunk_count, self.chunk_size, self.channels), np.float32)
                for i in range(0, self.chunk_count-1):
                    self.data_chunks[i] = self.file_data[self.chunk_size*(i):self.chunk_size*(i+1)]
                self.data_chunks[-1] = np.resize(self.file_data[self.chunk_size*(self.chunk_count-1):], (self.chunk_size, self.channels))
                
                self.playback_slider.setRange(0, self.chunk_count)
                if reset: self.frame = 0
                self.is_playing = True

        except Exception as e:
            print(f'File read error', e)
            self.seek(1)


    def set_audio(self, reset=True):
        self.is_playing = False
        self.playlist.setCurrentRow(self.playlist_index)
        name = self.playlist.currentItem().text()
        self.playing_label.setText(f'Playing: {self.playlist_index+1}. {name}')

        if self.current_playlist_data['type'] == 'local':
            self.file_path = Path(self.current_playlist_data['items'][name])

        elif self.current_playlist_data['type'] == 'url':
            self.file_path = (self.PATH/'tmp'/'audio'/f'{name}.opus')

            if not self.file_path.exists():
                audio_info = {'name': name, 'url': self.current_playlist_data['items'][name]}
                process = self.download.download_audios([audio_info], prioritise=True)
                process.join()

            self.process_download_ahead()

        self.read_audio_file(reset)


    def process_download_ahead(self):
        behind = self.current_playlist_data['delete_behind']
        ahead = self.current_playlist_data['download_ahead']
        if self.playlist_index-behind < 0: behind = self.playlist_index
        if self.playlist_index+ahead >= self.playlist.count(): ahead = self.playlist.count() - self.playlist_index - 1

        self.tmp_files = {}
        for i in range(-behind, ahead+1):
            name = self.playlist.item(self.playlist_index+i).text()
            self.tmp_files[name] = (self.PATH/'tmp'/'audio'/f'{name}.opus')

        audio_infos = []
        for name in self.tmp_files:
            if not self.tmp_files[name].exists():
                audio_infos.append({'name': name, 'url': self.current_playlist_data['items'][name]})
        
        for file in (self.PATH/'tmp'/'audio').iterdir():
            if file not in self.tmp_files.values():
                file.unlink()

        self.download.download_audios(audio_infos)


    def seek(self, amount):
        self.playlist_index = (self.playlist_index+amount) % self.playlist.count()
        self.set_audio()


    def play_toggle(self):
        if self.is_playing:
            play_button_icon = QPixmap(f"{self.PATH}/res/images/play-1001-minimalui-white.webp")
            self.play_button.setIcon(play_button_icon)
            self.is_playing = False
        else:
            play_button_icon = QPixmap(f"{self.PATH}/res/images/pause-button-icooon-white.webp")
            self.play_button.setIcon(play_button_icon)
            self.is_playing = True

            if self.frame >= self.chunk_count:
                self.playback_slider.setValue(0)
                self.frame = self.playback_slider.value()


    def update_chunk_size(self, size, set_plot_data):
        self.stream.abort()
        chunk_size_ratio = size/self.chunk_size
        self.chunk_size = size
        set_plot_data(True)
        self.stream = sd.Stream(samplerate=self.sr, blocksize=self.chunk_size, dtype=np.float32, channels=self.channels, callback=self.callback, latency='low')
        current_frame = int(self.frame // chunk_size_ratio)  # Calc before set_audio because slider breaks stuff past half of it for some reason
        self.set_audio(False)
        self.frame = current_frame
        self.stream.start()


    def set_using_mic(self, val):
        self.settings_data['using_mic'] = val
        self.save_data()


    def callback(self, indata, outdata, frames, time, status):
        total_data = np.zeros((self.chunk_size, self.channels), dtype=np.float32)
        
        if self.is_playing:
            if self.frame >= self.chunk_count:
                self.is_playing = False
                self.seek(1)
                return
            
            outdata[:self.chunk_size] = self.data_chunks[self.frame]*self.settings_data['volume']  # interesting I can't set it directly but i have to add [:chunk_size] 
            total_data += self.data_chunks[self.frame]

            self.frame += 1
            self.playback_slider.setValue(self.frame)
        else:
            outdata[:self.chunk_size] = 0

        if self.settings_data['using_mic']:
            total_data += indata

        self.update_plots(total_data, self.audio_avg)


class Delegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.text = f"{index.row() + 1}. {option.text}"


class Slider(QSlider):
    def mousePressEvent(self, event):
        super(Slider, self).mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            val = self.pixelPosToRangeValue(event.pos())
            self.setValue(val)


    def pixelPosToRangeValue(self, pos):
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        gr = self.style().subControlRect(QStyle.CC_Slider,
                                         opt, QStyle.SC_SliderGroove, self)
        sr = self.style().subControlRect(QStyle.CC_Slider,
                                         opt, QStyle.SC_SliderHandle, self)

        if self.orientation() == Qt.Horizontal:
            sliderLength = sr.width()
            sliderMin = gr.x()
            sliderMax = gr.right() - sliderLength + 1
        else:
            sliderLength = sr.height()
            sliderMin = gr.y()
            sliderMax = gr.bottom() - sliderLength + 1
        pr = pos - sr.center() + sr.topLeft()
        p = pr.x() if self.orientation() == Qt.Horizontal else pr.y()
        return QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), p - sliderMin,
                                                        sliderMax - sliderMin, opt.upsideDown)