from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QTabWidget
from PySide6.QtGui import QFont, QFontDatabase, QPixmap
from PySide6.QtCore import QTimer, Qt
from pathlib import Path
import sys
from lib.Playback import Playback
from lib.Playlists import Playlists
# from lib.Record import Record
from lib.Graph2D import Graph2D
# from lib.Graph3D import Graph3D
# from lib.Animation import Animation
# from lib.Nano import Nano
from lib.Download import Download
# import time


class XMV:
    def __init__(self):
        self.PATH = Path(__file__).parent

        # Window and app
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
        self.win.setWindowIcon(QPixmap(f"{self.PATH}/res/images/xmv_logo_x32.webp"))
        self.win.setTabPosition(Qt.DockWidgetArea.AllDockWidgetAreas, QTabWidget.TabPosition.North)
        self.win.setStyleSheet("* {background-color: #111111; color: white;} QTabBar:tab {background-color: #222222;}")

        # Create layout
        self.create_layout()

        # Download Manager
        self.download = Download(self.PATH)
    
        # Docks
        self.playlists = Playlists(self.win, self.PATH, self.download)
        self.playback = Playback(self.win, self.PATH, self.update_plots, self.download)

        self.graph2d = Graph2D(self.win)

        self.playback.playlist.setFont(QFont(self.fonts['nova_square'][0], 20))
        
        self.win.resizeDocks([self.graph2d.top_dock, self.graph2d.bottom_dock], [450, 600], Qt.Orientation.Vertical)
        self.win.tabifyDockWidget(self.graph2d.bottom_dock, self.playlists.dock)
        self.win.tabifyDockWidget(self.graph2d.bottom_dock, self.playback.dock)

        # Animation timer
        self.timer = QTimer(self.win)
        self.timer.timeout.connect(self.graph2d.update_plot)
        self.timer.start(10)

        self.win.showFullScreen()


    def import_fonts(self, paths):
        fonts = {}
        for path in paths:
            font_name = path.split('/')[-2]
            font_id = QFontDatabase.addApplicationFont(path)
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            fonts[font_name] = font_families
        return fonts


    def create_layout(self):
        def fullscreen_toggle():
            if self.win.windowState() != Qt.WindowState.WindowFullScreen:
                self.win.setWindowState(Qt.WindowState.WindowFullScreen)
            else:
                self.win.setWindowState(Qt.WindowState.WindowNoState)


        # Menubar
        menu_layout = QHBoxLayout(spacing=10)
        menu_layout.setContentsMargins(8,8,8,8)
        menu_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        menu_logo = QPixmap(f"{self.PATH}/res/images/xmv_logo_x32.webp")
        menu_logo_label = QLabel(pixmap=menu_logo)
        menu_layout.addWidget(menu_logo_label)
        
        menu_title = QLabel(text='XzistMusicVisualizer')
        menu_title.setFont(QFont(self.fonts['sans_mateo'][0], 24))
        menu_layout.addWidget(menu_title)

        menu_layout.addStretch(1)

        menu_fullscreen_button = QPushButton(text='FULLSCREEN')
        menu_fullscreen_button.pressed.connect(fullscreen_toggle)
        menu_layout.addWidget(menu_fullscreen_button)
        
        # Add seperation between menubar and contents
        menu_seperation_layout = QVBoxLayout()
        menu_seperation_layout.addLayout(menu_layout)
        menu_seperation_layout.setContentsMargins(0,0,0,8)

        # Merge widget and layouts
        menu_seperation_widget = QWidget(layout=menu_seperation_layout)
        menu_seperation_widget.setStyleSheet("background: #050505; color: white;")
        self.win.setMenuWidget(menu_seperation_widget)

        # Empty QWidget Hack
        self.win.setCentralWidget(QWidget(maximumHeight=0))


    # def set_mic(self):
    #     self.playback.is_use_mic = True


    def update_plots(self, indata):
        self.graph2d.update_data(indata)


    def run(self):
        if (sys.flags.interactive != 1):  # or not hasattr(pg.QtCore, 'PYQT_VERSION')
            with self.playback.stream:
                self.app.instance().exec()


if __name__ == '__main__':
    XMV().run()