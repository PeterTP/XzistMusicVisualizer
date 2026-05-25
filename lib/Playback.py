from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QDockWidget, QWidget, QListWidget, QCheckBox
from PySide6.QtCore import Qt
import json
import random
from pathlib import Path
import numpy as np
import sounddevice as sd
import soundfile as sf
import pyloudnorm as pyln
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

        self.stream = sd.Stream(samplerate=self.sr, blocksize=self.chunk_size, dtype=np.float32, channels=self.channels, callback=self.callback, latency='low')

        self.create_dock()
        self.update_playlist()

    
    def create_dock(self):
        def select_playlist():
            self.update_playlist(self.playlists_list.currentItem().text())


        def select_audio():
            self.playlist_index = self.playlist.currentRow()
            self.set_audio()


        def set_playback():
            self.frame = self.playback_slider.value()


        def set_volume():
            self.settings_data['volume'] = self.volume_slider.value()/100
            # TODO update settings


        def toggle_shuffle():
            copied_list = list(self.current_playlist_data['items'].copy())

            if shuffle_checkbox.isChecked():
                self.playlist.clear()
                self.playlist.addItems(copied_list) 
            else:
                random.shuffle(copied_list)
                self.playlist.clear()
                self.playlist.addItems(copied_list)


        # Playback lists
        self.playlists_list = QListWidget(flow=QListWidget.Flow.LeftToRight, spacing=4)
        self.playlists_list.setMinimumHeight(50)
        self.playlists_list.pressed.connect(select_playlist)

        self.playlist = QListWidget()
        self.playlist.pressed.connect(select_audio)

        # Playback seek and volume sliders
        playback_layout = QHBoxLayout()

        self.playback_slider = QSlider(Qt.Orientation.Horizontal)
        self.playback_slider.setRange(0, self.chunk_count)
        self.playback_slider.valueChanged.connect(set_playback)
        playback_layout.addWidget(self.playback_slider)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(set_volume)
        playback_layout.addWidget(self.volume_slider)

        # Buttons
        playback_buttons_layout = QHBoxLayout()

        back_button = QPushButton(text='<')
        back_button.pressed.connect(lambda: self.seek(-1))
        playback_buttons_layout.addWidget(back_button)

        self.play_button = QPushButton(text='||')
        self.play_button.pressed.connect(self.play_toggle)
        playback_buttons_layout.addWidget(self.play_button)

        forward_button = QPushButton(text='>')
        forward_button.pressed.connect(lambda: self.seek(1))
        playback_buttons_layout.addWidget(forward_button)

        shuffle_checkbox = QCheckBox(text='~')
        shuffle_checkbox.pressed.connect(toggle_shuffle)
        playback_buttons_layout.addWidget(shuffle_checkbox)

        # Merge widget and layouts
        playback_box_layout = QVBoxLayout()
        playback_box_layout.addWidget(self.playlists_list, 1)
        playback_box_layout.addWidget(self.playlist, 6)
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

        if self.current_playlist_data['type'] == 'local':
            # self.current_playlist_data['items'] will hold local file paths
            for item in Path(self.current_playlist_data['path']).iterdir():
                name = item.stem
                self.playlist.addItem(name)
                self.current_playlist_data['items'][name] = str(item)
            
            self.save_data()
        else:
            # self.current_playlist_data['items'] will hold urls
            GetPlaylistInfo().get_playlist_info(self.current_playlist_data['path'], update_items, update_complete, cache_last_updated=self.current_playlist_data['last_updated'])
            self.playlist.addItems(list(self.current_playlist_data['items']))

        self.volume_slider.setValue(self.settings_data['volume']*100)
        self.set_audio()


    def save_data(self):
        self.playlists_data['Playlists']['lists'][self.playlists_data['Playlists']['current']] = self.current_playlist_data
        self.playlists_data['Playback'] = self.settings_data

        with open(self.PATH/'res'/'data.json', 'w', encoding='utf-8') as f:
            json.dump(self.playlists_data, f, ensure_ascii=False, indent=4)


    def read_audio_file(self):
        try:
            if self.file_path.exists():
                self.file_data, self.sr = sf.read(self.file_path, dtype=np.float32)

                meter = pyln.Meter(self.sr)
                loudness = meter.integrated_loudness(self.file_data)
                self.file_data = pyln.normalize.loudness(self.file_data, loudness, -12.0)

                self.chunk_count = len(self.file_data)//self.chunk_size+1
                self.channels = self.file_data.shape[1]

                # Split file data into chunks
                self.data_chunks = np.zeros((self.chunk_count, self.chunk_size, self.channels), np.float32)
                for i in range(0, self.chunk_count-1):
                    self.data_chunks[i] = self.file_data[self.chunk_size*(i):self.chunk_size*(i+1)]
                self.data_chunks[-1] = np.resize(self.file_data[self.chunk_size*(self.chunk_count-1):], (self.chunk_size, self.channels))
                
                self.playback_slider.setRange(0, self.chunk_count)
                self.frame = 0
                self.playback_slider.setValue(0)
                self.is_playing = True

        except Exception as e:
            print(f'File read error', e)
            self.seek(1)


    def set_audio(self):
        self.is_playing = False
        name = self.playlist.item(self.playlist_index).text()

        if self.current_playlist_data['type'] == 'local':
            self.file_path = Path(self.current_playlist_data['items'][name])

        elif self.current_playlist_data['type'] == 'url':
            self.file_path = (self.PATH/'tmp'/f'{name}.opus')

            if not self.file_path.exists():
                audio_info = {'name': name, 'url': self.current_playlist_data['items'][name]}
                process = self.download.download_audios([audio_info], prioritise=True)
                process.join()

            self.process_download_ahead()

        self.read_audio_file()


    def process_download_ahead(self):
        behind = self.current_playlist_data['delete_behind']
        ahead = self.current_playlist_data['download_ahead']
        if self.playlist_index-behind < 0: behind = self.playlist_index
        if self.playlist_index+ahead >= self.playlist.count(): ahead = self.playlist.count() - self.playlist_index - 1

        self.tmp_files = {}
        for i in range(-behind, ahead+1):
            name = self.playlist.item(self.playlist_index+i).text()
            self.tmp_files[name] = (self.PATH/'tmp'/f'{name}.opus')

        audio_infos = []
        for name in self.tmp_files:
            if not self.tmp_files[name].exists():
                audio_infos.append({'name': name, 'url': self.current_playlist_data['items'][name]})
        
        for file in (self.PATH/'tmp').iterdir():
                if file not in self.tmp_files.values():
                    file.unlink()

        self.download.download_audios(audio_infos)


    def seek(self, amount):
        self.playlist_index = (self.playlist_index+amount) % self.playlist.count()
        self.set_audio()


    def play_toggle(self):
        if self.is_playing:
            self.play_button.setText('>')
            self.is_playing = False
        else:
            self.play_button.setText('||')
            self.is_playing = True

            if self.frame >= self.chunk_count:
                self.playback_slider.setValue(0)
                self.frame = self.playback_slider.value()


    def callback(self, indata, outdata, frames, time, status):
        total_data = np.zeros((self.chunk_size, self.channels), dtype=np.float32)
        
        if self.is_playing:
            if self.frame >= self.chunk_count:
                # self.play_toggle()
                self.is_playing = False
                self.seek(1)
                return
            
            outdata[:self.chunk_size] = self.data_chunks[self.frame]*self.settings_data['volume']  # interesting I can't set it directly but i have to add [:chunk_size] 
            total_data += self.data_chunks[self.frame]

            self.frame += 1
            self.playback_slider.setValue(self.frame)
        else:
            outdata[:self.chunk_size] = 0

        if self.settings_data['is_use_mic']:
            total_data += indata

        self.update_plots(total_data)