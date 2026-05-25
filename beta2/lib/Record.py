from PySide6.QtWidgets import QDockWidget, QCheckBox, QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QMargins, QTimer
import json

class Record():
    def __init__(self, win, PATH, set_using_mic, export):
        self.win = win
        self.PATH = PATH
        self.set_using_mic = set_using_mic
        self.export = export

        self.frame = 0
        self.video_timer = QTimer()
 
        self.create_dock()


    def create_dock(self):
        def export_frame():
            self.export(self.frame)
            self.frame += 1


        def record_video():
            if vid_checkbox.isChecked():
                self.frame = 0
                self.video_timer.start(50/3) # 60 fps
                self.video_timer.timeout.connect(export_frame)
            else:
                self.video_timer.stop()


        content_margins = QMargins(12, 12, 12, 12)

        mic_layout = QHBoxLayout()
        mic_layout.setContentsMargins(content_margins)
        mic_label = QLabel(text='Voice Input  ')
        mic_layout.addWidget(mic_label)
        mic_checkbox = QCheckBox()
        mic_checkbox.setChecked(True)
        mic_checkbox.clicked.connect(lambda: self.set_using_mic(mic_checkbox.isChecked()))
        mic_layout.addWidget(mic_checkbox)
        mic_layout.addStretch()

        with open(self.PATH/'res'/'data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            mic_checkbox.setChecked(data['Playback']['using_mic'])

        vid_layout = QHBoxLayout()
        vid_layout.setContentsMargins(content_margins)
        vid_label = QLabel(text='Record Video Frames  ')
        vid_layout.addWidget(vid_label)
        vid_checkbox = QCheckBox()
        vid_checkbox.setChecked(False)
        vid_checkbox.clicked.connect(record_video)
        vid_layout.addWidget(vid_checkbox)
        vid_layout.addStretch()

        record_box_layout = QVBoxLayout()
        record_box_layout.addLayout(mic_layout)
        record_box_layout.addLayout(vid_layout)

        record_box_widget = QWidget(layout=record_box_layout)

        self.dock = QDockWidget('RECORD', widget=record_box_widget)
        self.win.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dock)