from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QDockWidget, QWidget, QListWidget, QAbstractItemView, QMessageBox, QFileDialog, QTextEdit, QCheckBox, QRadioButton, QSpinBox
from PySide6.QtCore import Qt
import json


class Playlists:
    def __init__(self, win, PATH, download):
        self.win = win
        self.PATH = PATH
        self.download = download

        self.editing_name = ""

        with open(self.PATH/'res'/'data.json', 'r', encoding='utf-8') as f:
            self.playlists_data = json.load(f)

        self.create_dock()


    def create_dock(self):
        def select():
            list_data = self.playlists_data['Playlists']['lists'][playlists_list.currentItem().text()]

            path_input.setText(list_data['path'])
            if list_data['type'] == 'url':
                url_radio.setChecked(True)
                download_ahead_input.setValue(list_data['download_ahead'])
                delete_behind_input.setValue(list_data['delete_behind'])
            else:
                url_radio.setChecked(False)

            self.editing_name = playlists_list.currentItem().text()


        def add():
            name = 'New Playlist'
            i = 2
            while name in list(self.playlists_data['Playlists']['lists']):
                name = f'New Playlist {i}'
                i += 1

            self.playlists_data['Playlists']['lists'][name] = {
                'type': 'local',
                'path': f'{str(self.PATH)}/tmp',
                "items": {}
            }
            playlists_list.addItem(name)
            item = playlists_list.item(playlists_list.count()-1)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)

            with open(self.PATH/'res'/'data.json', 'w', encoding='utf-8') as f:
                json.dump(self.playlists_data, f, ensure_ascii=False, indent=4)


        def remove():
            ans = remove_msg_box.exec()

            if ans == QMessageBox.StandardButton.Yes:
                self.playlists_data['Playlists']['lists'].pop(playlists_list.currentItem().text())
                playlists_list.takeItem(playlists_list.currentRow())

                with open(self.PATH/'res'/'data.json', 'w', encoding='utf-8') as f:
                    json.dump(self.playlists_data, f, ensure_ascii=False, indent=4)


        def edit():
            playlists_list.editItem(playlists_list.currentItem())


        def edited():
            # Handles editing name
            if self.editing_name:
                playlist = self.playlists_data['Playlists']['lists'].pop(self.editing_name)
                self.playlists_data['Playlists']['lists'][playlists_list.currentItem().text()] = playlist
                self.editing_name = playlists_list.currentItem().text()

                with open(self.PATH/'res'/'data.json', 'w', encoding='utf-8') as f:
                    json.dump(self.playlists_data, f, ensure_ascii=False, indent=4)
            

        def moved():
            # Handles moving indexes
            new_playlists = {}

            for i in range(playlists_list.count()):
                name = playlists_list.item(i).text()
                new_playlists[name] = self.playlists_data['Playlists']['lists'][name]
            
            self.playlists_data['Playlists']['lists'] = new_playlists

            with open(self.PATH/'res'/'data.json', 'w', encoding='utf-8') as f:
                json.dump(self.playlists_data, f, ensure_ascii=False, indent=4)


        def select_path():
            if (path_dialog.exec()):
                path_input.setText(path_dialog.selectedFiles()[0])


        def url_local_select():
            if url_radio.isChecked():
                path_input.setPlaceholderText('Enter a playlist url')
                path_button.hide()
                download_check.hide()
                url_input.hide()
                download_log_text.hide()
                download_button.hide()
                download_ahead_input.show()
                delete_behind_input.show()
            else:
                path_input.setPlaceholderText('Enter a local path')
                path_button.show()
                download_check.show()
                show_download()
                download_ahead_input.hide()
                delete_behind_input.hide()
                

        def show_download():
            if download_check.isChecked():
                url_input.show()
                download_log_text.show()
                download_button.show()
            else:
                url_input.hide()
                download_log_text.hide()
                download_button.hide()


        def init_download():
            self.download.batch_download_audios(url_input.text(), path_input.text())


        def confirm():
            list_data = self.playlists_data['Playlists']['lists'][playlists_list.currentItem().text()]

            list_data['path'] = path_input.text()
            if url_radio.isChecked():
                list_data['type'] = 'url'
                list_data['download_ahead'] = download_ahead_input.value()
                list_data['delete_behind'] = delete_behind_input.value()
            else:
                list_data['type'] = 'local'

            with open(self.PATH/'res'/'data.json', 'w', encoding='utf-8') as f:
                json.dump(self.playlists_data, f, ensure_ascii=False, indent=4)


        # Playlists list
        playlists_list = QListWidget(spacing=4)
        playlists_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

        for playlist in self.playlists_data['Playlists']['lists']:
            playlists_list.addItem(playlist)
            item = playlists_list.item(playlists_list.count()-1)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)

        playlists_list.pressed.connect(select)
        playlists_list.itemChanged.connect(edited)
        playlists_list.model().rowsMoved.connect(moved)
        
        # Playlists buttons and message box
        playlist_buttons_layout = QVBoxLayout()

        add_button = QPushButton(text='+')
        add_button.clicked.connect(add)
        playlist_buttons_layout.addWidget(add_button)

        remove_msg_box = QMessageBox(text='Are you sure you want to remove this playlist?')
        remove_msg_box.setWindowTitle('Remove Playlist')
        remove_msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        remove_button = QPushButton(text='x')
        remove_button.clicked.connect(remove)
        playlist_buttons_layout.addWidget(remove_button)

        edit_button = QPushButton(text='I')
        edit_button.clicked.connect(edit)
        playlist_buttons_layout.addWidget(edit_button)

        # Playlist settings
        playlist_settings_layout = QVBoxLayout()

        # Input field and button
        local_radio = QRadioButton(text='Local', checked=True)
        local_radio.toggled.connect(url_local_select)
        playlist_settings_layout.addWidget(local_radio)

        url_radio = QRadioButton(text='Url')
        url_radio.toggled.connect(url_local_select)
        playlist_settings_layout.addWidget(url_radio)

        # Path input, button and dialog
        path_input = QLineEdit(PlaceholderText='Enter a local path')
        playlist_settings_layout.addWidget(path_input)

        path_dialog = QFileDialog()
        path_dialog.setFileMode(QFileDialog.FileMode.Directory)

        path_button = QPushButton(text='CHOOSE FOLDER')
        path_button.pressed.connect(select_path)
        playlist_settings_layout.addWidget(path_button)

        # Batch Download
        download_check = QCheckBox(text='BATCH DOWNLOAD')
        download_check.toggled.connect(show_download)
        playlist_settings_layout.addWidget(download_check)

        # Url input
        url_input = QLineEdit(PlaceholderText='Enter a playlist url', hidden=True)
        playlist_settings_layout.addWidget(url_input)

        download_button = QPushButton(text='DOWNLOAD', hidden=True)
        download_button.pressed.connect(init_download)
        playlist_settings_layout.addWidget(download_button)

        # Download Log
        download_log_text = QTextEdit(readOnly=True, hidden=True)
        playlist_settings_layout.addWidget(download_log_text)

        # Url options
        download_ahead_input = QSpinBox(minimum=0, maximum=9, hidden=True)
        playlist_settings_layout.addWidget(download_ahead_input)

        delete_behind_input = QSpinBox(minimum=0, maximum=9, hidden=True)
        playlist_settings_layout.addWidget(delete_behind_input)

        # Confirm
        confirm_button = QPushButton(text='CONFIRM')
        confirm_button.pressed.connect(confirm)
        playlist_settings_layout.addWidget(confirm_button)

        # Merge widget and layouts
        playlists_layout = QHBoxLayout()
        playlists_layout.addWidget(playlists_list)
        playlists_layout.addLayout(playlist_buttons_layout)
        playlists_layout.addLayout(playlist_settings_layout)
        playlists_box_widget = QWidget(layout=playlists_layout)

        self.dock = QDockWidget('Playlists', widget=playlists_box_widget)
        self.win.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dock)